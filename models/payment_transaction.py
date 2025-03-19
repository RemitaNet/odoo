# -*- coding: utf-8 -*-
# Part 4: Payment Transaction Model

import logging
import requests
import pprint
import json
import hashlib
from datetime import datetime

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    remita_payment_reference = fields.Char('Remita Payment Reference')
    remita_rrr = fields.Char('Remita Retrieval Reference Number')

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override to handle data from Remita webhooks. """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'remita':
            return tx

        reference = data.get('reference')
        rrr = data.get('rrr')
        if not reference and not rrr:
            error_msg = "Remita: " + _("Received data with missing reference or RRR")
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        if reference:
            tx = self.search([('reference', '=', reference), ('provider', '=', 'remita')])
        elif rrr:
            tx = self.search([('remita_rrr', '=', rrr), ('provider', '=', 'remita')])

        if not tx:
            error_msg = "Remita: " + _("No transaction found matching reference %s or RRR %s.", reference, rrr)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _process_feedback_data(self, data):
        """ Override to process the transaction based on Remita data. """
        super()._process_feedback_data(data)
        if self.provider != 'remita':
            return

        status = data.get('status', '').upper()
        if status == 'SUCCESSFUL' or status == 'SUCCESS':
            self._set_done()
        elif status == 'FAILED':
            self._set_canceled("Remita: " + _("Payment failed."))
        elif status == 'PENDING':
            self._set_pending()
        else:
            _logger.info("Remita: received data with invalid status: %s", status)
            self._set_error("Remita: " + _("Received unrecognized status: %s", status))

    def _get_specific_rendering_values(self, processing_values):
        """ Override for remita-specific rendering values. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'remita':
            return res

        acquirer_sudo = self.acquirer_id.sudo()
        amount = processing_values['amount']
        currency = self.currency_id
        partner = self.partner_id

        # Create the payload for Remita
        payload = {
            'merchantId': acquirer_sudo.remita_merchant_id,
            'serviceTypeId': acquirer_sudo.remita_service_type_id,
            'orderId': self.reference,
            'amount': str(int(amount * 100)),  # Convert to smallest currency unit
            'payerName': partner.name,
            'payerEmail': partner.email or '',
            'payerPhone': partner.phone or '',
            'description': f"Payment for order {self.reference}",
        }

        # Add the hash
        api_key = acquirer_sudo.remita_api_key
        hash_string = f"{acquirer_sudo.remita_merchant_id}{acquirer_sudo.remita_service_type_id}{self.reference}{str(int(amount * 100))}{api_key}"
        payload['hash'] = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        payload['responseurl'] = urls.url_join(base_url, '/payment/remita/return')

        rendering_values = {
            'merchant_id': acquirer_sudo.remita_merchant_id,
            'service_type_id': acquirer_sudo.remita_service_type_id,
            'tx_ref': self.reference,
            'amount': amount,
            'public_key': acquirer_sudo.remita_api_key,
            'currency': currency.name,
            'customer_email': partner.email,
            'customer_name': partner.name,
            'payment_options': 'card,ussd,transfer',
            'redirect_url': payload['responseurl'],
            'js_url': acquirer_sudo._get_remita_inline_js_url(),
            'payload': json.dumps(payload),
        }

        return rendering_values
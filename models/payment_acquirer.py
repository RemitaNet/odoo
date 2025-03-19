# -*- coding: utf-8 -*-
# Part 3: Payment Acquirer Model

import logging
import requests
import hashlib
import json
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('remita', 'Remita')],
        ondelete={'remita': 'set default'}
    )
    remita_merchant_id = fields.Char(
        string="Merchant ID",
        help="The merchant ID provided by Remita",
        required_if_provider='remita'
    )
    remita_api_key = fields.Char(
        string="API Key",
        help="The API key provided by Remita",
        required_if_provider='remita'
    )
    remita_service_type_id = fields.Char(
        string="Service Type ID",
        help="The service type ID provided by Remita",
        required_if_provider='remita'
    )
    remita_mode = fields.Selection(
        [('Test', 'Test'), ('Live', 'Live')],
        string="Remita Environment",
        default='Test',
        required_if_provider='remita'
    )

    def _get_remita_api_url(self):
        """ Return the appropriate URL for the environment """
        if self.remita_mode == 'Test':
            return 'https://remitademo.net/remita/exapp/api/v1/send/api'
        else:
            return 'https://login.remita.net/remita/exapp/api/v1/send/api'
    
    def _get_remita_inline_js_url(self):
        """ Return the appropriate JS URL for the environment """
        if self.remita_mode == 'Test':
            return 'https://demo.remita.net/payment/v1/remita-pay-inline.bundle.js'
        else:
            return 'https://login.remita.net/payment/v1/remita-pay-inline.bundle.js'

    def _compute_remita_hash(self, amount, ref, service_type_id, api_key):
        """Compute the hash for Remita API authentication"""
        concat_string = f"{merchant_id}{service_type_id}{ref}{amount}{api_key}"
        return hashlib.sha512(concat_string.encode('utf-8')).hexdigest()

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'remita':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_remita.payment_method_remita').id
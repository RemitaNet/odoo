# -*- coding: utf-8 -*-
# Part 6: Controllers Implementation

import logging
import pprint
import werkzeug
import json
import hmac
import hashlib

from odoo import http
from odoo.http import request
from odoo.addons.payment.controllers.portal import PaymentPortal

_logger = logging.getLogger(__name__)

class RemitaController(http.Controller):
    
    @http.route('/payment/remita/return', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def remita_return(self, **post):
        """ Process the data received from Remita after customer payment """
        _logger.info("Remita return data: %s", pprint.pformat(post))
        
        # Extract data from the return
        reference = post.get('orderID')
        rrr = post.get('RRR')
        status = post.get('status')
        
        if not reference:
            _logger.error("Remita: No reference found in return data")
            return werkzeug.utils.redirect('/payment/status')
        
        # Format the data for processing
        feedback_data = {
            'reference': reference,
            'rrr': rrr,
            'status': status,
        }
        
        request.env['payment.transaction'].sudo()._handle_feedback_data('remita', feedback_data)
        return werkzeug.utils.redirect('/payment/status')
    
    @http.route('/payment/remita/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def remita_webhook(self):
        """ Process the webhook notifications from Remita """
        data = json.loads(request.httprequest.data)
        _logger.info("Remita webhook data: %s", pprint.pformat(data))
        
        # Verify webhook signature
        if not self._verify_remita_signature(request):
            _logger.error("Remita: Invalid webhook signature")
            return {'status': 'error', 'message': 'Invalid signature'}
        
        reference = data.get('orderID')
        rrr = data.get('RRR')
        status = data.get('status')
        
        # Format the data for processing
        feedback_data = {
            'reference': reference,
            'rrr': rrr,
            'status': status,
        }
        
        try:
            request.env['payment.transaction'].sudo()._handle_feedback_data('remita', feedback_data)
            return {'status': 'success'}
        except Exception as e:
            _logger.exception("Error processing Remita webhook: %s", str(e))
            return {'status': 'error', 'message': str(e)}
    
    def _verify_remita_signature(self, request):
        """Verify the webhook signature sent by Remita"""
        # Implementation depends on how Remita sends the webhook signature
        # Below is a generic implementation that should be customized
        
        data = request.httprequest.data
        received_signature = request.httprequest.headers.get('X-Remita-Signature')
        
        if not received_signature:
            return False
        
        # Get the active Remita payment acquirer
        acquirer = request.env['payment.acquirer'].sudo().search([('provider', '=', 'remita')], limit=1)
        if not acquirer:
            return False
        
        # Calculate expected signature using the API key
        api_key = acquirer.remita_api_key
        expected_signature = hmac.new(
            api_key.encode('utf-8'),
            data,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(received_signature, expected_signature)
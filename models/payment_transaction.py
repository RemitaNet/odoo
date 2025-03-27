from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    remita_transaction_id = fields.Char(
        string='Remita Transaction ID', 
        help='Unique identifier for the Remita transaction',
        copy=False
    )

    def _get_specific_rendering_values(self, processing_values):
        """
        Prepare transaction-specific rendering values for Remita.
        This method is called when initiating a payment.
        """
        if self.provider_code != 'remita':
            return {}

        provider = self.provider_id
        
        rendering_values = {
            'provider': provider,
            'public_key': provider.remita_public_key,
            'transaction_id': self.reference,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'mode': provider.remita_mode,
        }

        return rendering_values

    def _process_feedback_data(self, data):
        """
        Process the payment feedback/webhook data from Remita.
        Validate transaction status and update accordingly.
        """
        if self.provider_code != 'remita':
            return super()._process_feedback_data(data)

        # Example validation logic - adapt to Remita's actual webhook response
        try:
            transaction_status = data.get('status')
            remita_transaction_id = data.get('transaction_id')

            if transaction_status == 'successful':
                self._set_done()
                self.remita_transaction_id = remita_transaction_id
            elif transaction_status == 'failed':
                self._set_canceled()
            else:
                self._set_pending()

        except Exception as e:
            _logger.error(f"Remita Transaction Processing Error: {e}")
            self._set_error(f"Payment validation failed: {e}")

        return {}

    @api.model
    def _get_tx_from_feedback_data(self, provider_code, data):
        """
        Find the transaction based on Remita's webhook data.
        """
        if provider_code != 'remita':
            return super()._get_tx_from_feedback_data(provider_code, data)

        # Example: Extract reference from Remita's webhook data
        reference = data.get('reference')
        if not reference:
            raise ValidationError("No transaction reference found in Remita webhook data")

        transaction = self.search([
            ('reference', '=', reference),
            ('provider_code', '=', 'remita')
        ])

        return transaction
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('remita', 'Remita')],
        ondelete={'remita': 'cascade'}
    )
    
    remita_public_key = fields.Char(
        string='Remita Public Key',
        help='The public key provided by Remita',
        groups='base.group_system'
    )
    
    remita_mode = fields.Selection([
        ('demo', 'Demo'),
        ('live', 'Live')
    ], string='Mode', default='demo')

    @api.constrains('code', 'remita_public_key')
    def _check_remita_configuration(self):
        """Validate Remita-specific configurations."""
        for provider in self:
            if provider.code == 'remita':
                if not provider.remita_public_key or provider.remita_public_key == 'placeholder_key':
                    # Allow creation, but warn that key needs to be updated
                    self.env.cr.savepoint()
                    # Optionally, log a warning
                    self.env['mail.message'].create({
                        'model': self._name,
                        'res_id': provider.id,
                        'message_type': 'notification',
                        'body': 'Remita Payment Provider created with placeholder key. Please update with a valid public key.',
                        'subtype_id': self.env.ref('mail.mt_note').id,
                    })

    def _get_remita_script_url(self):
        """Return the appropriate Remita script URL based on mode."""
        self.ensure_one()
        if self.remita_mode == 'demo':
            return 'https://demo.remita.net/payment/v1/remita-pay-inline.bundle.js'
        return 'https://login.remita.net/payment/v1/remita-pay-inline.bundle.js'

    def _compute_feature_support(self):
        """Define supported features for Remita."""
        super()._compute_feature_support()
        remita_providers = self.filtered(lambda p: p.code == 'remita')
        for provider in remita_providers:
            provider.update({
                'support_tokenization': False,
                'support_manual_capture': False,
            })

    @api.model
    def _get_default_payment_method_ids(self):
        """Link to a generic payment method."""
        res = super()._get_default_payment_method_ids()
        
        # For Remita, add card payment method
        remita_providers = self.search([('code', '=', 'remita')])
        if remita_providers:
            card_method = self.env.ref('payment.payment_method_card')
            if card_method:
                res |= card_method
        
        return res
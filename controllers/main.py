from odoo import http
from odoo.http import request

class RemitaController(http.Controller):

    @http.route('/payment/remita/initiate', type='http', auth='public', methods=['POST'], csrf=False)
    def remita_initiate(self, **post):
        provider = request.env['payment.provider'].sudo().search([('code', '=', 'remita')], limit=1)
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', post.get('reference'))])

        if not tx or not provider:
            return request.redirect('/shop/payment')

        # Prepare transaction data for the widget
        tx_values = {
            'key': provider.remita_public_key,
            'transactionId': tx.reference,  # Use Odoo's reference
            'customerId': tx.partner_id.id or 'guest',
            'firstName': tx.partner_id.name.split()[0] if tx.partner_id.name else 'Guest',
            'lastName': tx.partner_id.name.split()[-1] if tx.partner_id.name and len(tx.partner_id.name.split()) > 1 else '',
            'email': tx.partner_id.email or 'no-email@example.com',
            'amount': tx.amount,
            'narration': f'Payment for {tx.reference}',
        }

        return request.render('payment_remita.payment_widget', {
            'tx_values': tx_values,
            'script_url': provider._get_remita_script_url(),
            'return_url': '/payment/remita/return',
        })

    @http.route('/payment/remita/return', type='json', auth='public', methods=['POST'])
    def remita_return(self, **post):
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', post.get('reference'))])
        if not tx:
            return {'status': 'error', 'message': 'Transaction not found'}

        # Process response from Remita
        response = post.get('response', {})
        if response.get('status') == 'success':
            tx._set_transaction_done()
        elif response.get('status') == 'error':
            tx._set_transaction_error(response.get('message', 'Payment failed'))
        else:
            tx._set_transaction_pending()

        return {'status': 'success', 'redirect': '/payment/status'}
odoo.define('payment_remita.remita_widget', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.RemitaPaymentWidget = publicWidget.Widget.extend({
        selector: '#payment-form',
        events: {
            // No specific events needed here; we trigger on DOM load
        },

        // Initialize the widget
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._initRemitaPayment();
            });
        },

        _initRemitaPayment: function () {
            // Extract data from the DOM (passed via data attributes or hidden inputs)
            var $form = this.$el;
            var txData = {
                key: $form.data('remita-key'),
                transactionId: $form.data('transaction-id'),
                customerId: $form.data('customer-id'),
                firstName: $form.data('first-name'),
                lastName: $form.data('last-name'),
                email: $form.data('email'),
                amount: $form.data('amount'),
                narration: $form.data('narration'),
                returnUrl: $form.data('return-url')
            };

            // Ensure RmPaymentEngine is loaded
            if (typeof RmPaymentEngine === 'undefined') {
                console.error('Remita Payment Engine not loaded');
                window.location = txData.returnUrl;
                return;
            }

            // Initialize Remita Payment Engine
            var paymentEngine = RmPaymentEngine.init({
                key: txData.key,
                transactionId: txData.transactionId,
                customerId: txData.customerId,
                firstName: txData.firstName,
                lastName: txData.lastName,
                email: txData.email,
                amount: txData.amount,
                narration: txData.narration,
                onSuccess: function (response) {
                    self._handleCallback('success', response, txData.transactionId, txData.returnUrl);
                },
                onError: function (response) {
                    self._handleCallback('error', response, txData.transactionId, txData.returnUrl);
                },
                onClose: function () {
                    window.location = txData.returnUrl;
                }
            });

            // Show the payment widget
            paymentEngine.showPaymentWidget();
        },

        _handleCallback: function (status, response, reference, returnUrl) {
            var data = {
                reference: reference,
                response: { status: status, data: response }
            };
            fetch('/payment/remita/return', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(function () {
                window.location = returnUrl;
            }).catch(function (error) {
                console.error('Callback error:', error);
                window.location = returnUrl;
            });
        }
    });

    return publicWidget.registry.RemitaPaymentWidget;
});
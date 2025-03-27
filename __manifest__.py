{
    'name': 'Remita Payment Provider',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Integrate Remita as a payment provider in Odoo',
    'depends': ['payment'],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_remita/static/src/js/remita_widget.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
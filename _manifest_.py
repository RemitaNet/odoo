# -*- coding: utf-8 -*-
# Part 1: Module Definition and Initial Setup

{
    'name': 'Remita Payment Gateway',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Payment Acquirers',
    'summary': 'Payment Acquirer: Remita Implementation',
    'description': """
        Remita Payment Gateway Integration for Odoo.
        This module allows customers to make payments via Remita.
    """,
    'author': 'Mfonido Mark',
    'website': 'https://remita.net/',
    'depends': ['payment'],
    'data': [
        'views/payment_remita_templates.xml',
        'views/payment_views.xml',
        'data/payment_acquirer_data.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'post_init_hook': '_create_missing_journal_for_acquirers',
    'uninstall_hook': '_uninstall_hook',
    'license': 'LGPL-3',
}
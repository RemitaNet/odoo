# -*- coding: utf-8 -*-
# Part 7: Module Init File

from . import models
from . import controllers
from odoo.addons.payment import setup_provider, reset_payment_provider

def _create_missing_journal_for_acquirers(cr, registry):
    """Create the journal for existing acquirers"""
    setup_provider('remita')

def _uninstall_hook(cr, registry):
    """Uninstall hook to reset the payment provider"""
    reset_payment_provider('remita')
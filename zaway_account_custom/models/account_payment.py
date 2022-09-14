# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from dateutil.relativedelta import relativedelta
import time
from odoo import tools

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    currency_dealer = fields.Char(string="Currency Dealer")
    new_rate = fields.Float(string='New Rate')

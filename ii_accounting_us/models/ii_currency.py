# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2020-Today IATL IntelliSoft (<http://www.iatl-intellisoft.com>)#
###################################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# inherit to allow field for black market rate
class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    flat_rate = fields.Float('Flat Rate', default='1.0', required=True)

    @api.onchange('flat_rate')
    def get_rate(self):
        if self.flat_rate != 0:
            self.rate = 1 / self.flat_rate
        else:
            raise (_("Check your rate!"))



# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2020-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################

from odoo import fields, models, api

class Currency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        res = super(Currency,self)._get_conversion_rate(from_currency, to_currency, company, date)

        if self._context.get('custom_rate'):
            if self._context.get('custom_rate') > 1:
            	res = currency_rates.get(to_currency.id) / res

        return res

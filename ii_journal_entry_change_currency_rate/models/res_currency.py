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
        """override _get_conversion_rate(), to perform calculations based on custom rate
        """
        res = super(Currency,self)._get_conversion_rate(from_currency, to_currency, company, date)
        if self._context.get('custom_rate'):
            custom_rate = self._context.get('custom_rate')
            if custom_rate > 1:
                currency_rates = (from_currency + to_currency)._get_rates(company, date)
                res = currency_rates.get(to_currency.id) / custom_rate 

            return res

        else:
            return res


    # @api.model
    # def _get_conversion_rate(self, from_currency, to_currency, company, date):
    #     currency_rates = (from_currency + to_currency)._get_rates(company, date)
    #     res = super(Currency,self)._get_conversion_rate(from_currency, to_currency, company, date)

    #     if self._context.get('custom_rate'):
    #         if self._context.get('custom_rate') > 1:
    #             res = currency_rates.get(to_currency.id) / res
    #         return res
    #     else:
    #         return res
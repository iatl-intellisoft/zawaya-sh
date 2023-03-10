# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# Copyright 2015 Techrifiv Solutions Pte Ltd
# Copyright 2015 Statecraft Systems Pte Ltd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    rate_inverted = fields.Boolean(
        'Inverted exchange rate',
        company_dependent=True,default=True)

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        res = super(ResCurrency, self)._get_conversion_rate(from_currency, to_currency, company, date)
        return res

    # @api.model
    # def _get_conversion_rate(self, from_currency, to_currency):
    #     res = super(ResCurrency, self)._get_conversion_rate(from_currency,
    #                                                         to_currency)

    #     '''if (
    #         from_currency.rate_inverted and to_currency.rate_inverted or
    #             not from_currency.rate_inverted and
    #             not to_currency.rate_inverted):
    #         return res
    #     else:'''
    #         #return 1/res
    #     return 1/res

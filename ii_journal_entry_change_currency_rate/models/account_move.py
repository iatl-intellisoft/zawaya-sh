# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2020-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################

from odoo import fields, models, api

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    custom_rate = fields.Float('Custom Rate',default=1,help="Set new currency rate to apply on the payment")
    currency_rate = fields.Float('Currency Rate',help="Technical field used to get acctual Currency Rate As 1/custom_rate",compute="_get_currency_rate")

    @api.depends('custom_rate')
    def _get_currency_rate(self):
        """
        get acctual Currency Rate As 1/custom_rate
        """
        for rec in self:
            rec.currency_rate = 1/rec.custom_rate

    @api.onchange('amount_currency','custom_rate')
    def _onchange_amount_currency(self):
        """Overrides _onchange_amount_currency(), That Recompute the debit/credit
        based on amount_currency/currency_id and date to include custom rate in
        currency related calculations represented in the context
        """
        res = super(AccountMoveLine,self.with_context(custom_rate=self.custom_rate))._onchange_amount_currency()
        return res

    @api.onchange('currency_id')
    def _onchange_currency(self):
        """Overrides _onchange_currency() ,Update custom rate value on change of 
        currency_id/custom_rate values
        """

        move_type = self._context.get('default_type')
        for rec in self:
            res = super(AccountMoveLine,rec.with_context(custom_rate=rec.custom_rate))._onchange_currency()
            today = fields.Date.today()

            if rec.currency_id and move_type == 'entry':
                rec.custom_rate = rec.currency_id._get_conversion_rate(rec.currency_id, rec.move_id.company_id.currency_id, rec.move_id.company_id,rec.move_id.date or today)
            return res

    # @api.onchange('custom_rate')
    # def _onchange_custom_rate(self):
    #     for rec in self:
    #         rec.with_context(custom_rate=rec.currency_rate)._recompute_debit_credit_from_amount_currency()

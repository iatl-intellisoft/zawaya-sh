# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2020-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################

from odoo import fields, models, api

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    custom_rate = fields.Float('Currency Rate', help="Set new currency rate to apply on the invoice")
    currency_rate = fields.Float('Currency Rate',digits=(12, 6),help="Technical field used to get acctual Currency Rate As 1/custom_rate",compute="_get_currency_rate")

    @api.depends('custom_rate')
    def _get_currency_rate(self):
        """
        get acctual Currency Rate As 1/custom_rate
        """
        for rec in self:
            rec.currency_rate = 1/rec.custom_rate
            # rec.currency_rate = rec.currency_id.round(1/rec.custom_rate)

    def action_post(self):
        """Overrides post(), that Creates the journal items for the payment and
          update the move state to 'posted' with inclusion to custom rate
          to use in currency related calculations.
        """
        res = super(AccountInvoice,self.with_context(custom_rate=self.custom_rate)).action_post()
        return res


    # @api.onchange('currency_id','invoice_date')
    # def _onchange_currency_date(self):
    #     # Update custom rate value onchange of date value
    #     today = fields.Date.today()
    #     self.custom_rate = self.currency_id._get_conversion_rate(self.currency_id, self.company_id.currency_id, self.company_id,self.invoice_date or today)
    #     self._onchange_custom_rate()

    @api.onchange('custom_rate')
    def _onchange_custom_rate(self):
        for rec in self:
            if rec.move_type == 'entry':
                continue
            for line in rec.line_ids:
                line.custom_rate = rec.custom_rate
                line.with_context(custom_rate=rec.custom_rate)._onchange_amount_currency()

    @api.onchange('date', 'currency_id')
    def _onchange_currency(self):
        today = fields.Date.today()
        self.custom_rate = self.currency_id._get_conversion_rate(self.currency_id, self.company_id.currency_id,self.company_id, self.date or today)
        return super(AccountInvoice, self.with_context(custom_rate=self.custom_rate))._onchange_currency()

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        """
        Overwrite to add discount lines to move line
        """
        self._onchange_custom_rate()
        res = super(AccountInvoice, self.with_context(custom_rate=self.custom_rate))._recompute_dynamic_lines()
        return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    def _get_fields_onchange_subtotal(self, price_subtotal=None, move_type=None, currency=None, company=None, date=None):
        """Overrides _get_fields_onchange_subtotal(),Witch used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance' ,with inclusion to custom rate
        to use in currency related calculations. 
        """
        res = super(AccountMoveLine,self.with_context(custom_rate=self.currency_rate))._get_fields_onchange_subtotal(price_subtotal, move_type, currency, company, date)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """
        """
        for vals in vals_list:
            if vals.get('move_id', False):
                move = self.env['account.move'].browse(vals['move_id'])
                if move.custom_rate and move.move_type != 'entry':
                    vals['custom_rate'] = move.custom_rate
        return super(AccountMoveLine, self).create(vals_list)

    def write(self, vals):
        """
        """
        for rec in self:
            move_id = vals.get('move_id', rec.move_id.id)
            move = self.env['account.move'].browse(move_id)
            if move.custom_rate and move.move_type != 'entry':
                vals['custom_rate'] = move.custom_rate

        return super(AccountMoveLine, self).write(vals)

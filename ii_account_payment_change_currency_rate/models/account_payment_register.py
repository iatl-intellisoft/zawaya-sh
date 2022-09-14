# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError , ValidationError

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    custom_rate = fields.Float('Currency Rate',default=1.0,readonly=False, help="Set new currency rate to apply on the payment")


    @api.onchange('currency_id','payment_date')
    def _onchange_curreny_id_custom_rate(self):
        today = fields.Date.today()
        if self.currency_id:
            self.custom_rate = self.company_id.currency_id._get_conversion_rate(self.company_id.currency_id,self.currency_id, self.company_id, self.payment_date or today)
            # if base_rate:
            #     self.custom_rate = base_rate
            # else:
            #     self.custom_rate = 1    

    @api.onchange('custom_rate')
    def _onchange_currency_rate(self):

    	for wizard in self:
            if not(wizard.source_currency_id == wizard.currency_id or wizard.currency_id == wizard.company_id.currency_id):
                wizard.amount = wizard.source_amount * wizard.custom_rate


    def _create_payment_vals_from_wizard(self):
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids.filtered(lambda r: r.exclude_from_invoice_tab == True)[
                0].account_id.id
        }

        if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        payment_vals['custom_rate'] = self.custom_rate    

        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = self._get_wizard_values_from_batch(batch_result)
        return {
            'date': self.payment_date,
            'amount': batch_values['source_amount_currency'],
            'payment_type': batch_values['payment_type'],
            'partner_type': batch_values['partner_type'],
            'ref': self._get_batch_communication(batch_result),
            'journal_id': self.journal_id.id,
            'currency_id': batch_values['source_currency_id'],
            'partner_id': batch_values['partner_id'],
            'partner_bank_id': batch_result['key_values']['partner_bank_id'],
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': batch_result['lines'].filtered(lambda r: r.exclude_from_invoice_tab == True).account_id.id
        }

        # payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        # payment_vals['custom_rate'] = self.custom_rate

        # return payment_vals
    
    # becuase wrong when register payment for write off account 
    # def _create_payments(self):
    #     payments = super(AccountPaymentRegister, self.with_context(custom_rate=1/self.custom_rate))._create_payments()
    #     for payment in payments:
    #         payment.custom_rate = self.custom_rate
    #     return payments

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_post(self):
        ''' draft -> posted '''
        for rec in self:
            for line in rec.move_id.line_ids:
               line.custom_rate = rec.custom_rate
        return super(AccountPayment, self).action_post()



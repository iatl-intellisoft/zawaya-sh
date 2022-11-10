# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2020-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################

from odoo import fields, models, api


class account_payment(models.Model):
    _inherit = "account.payment"

    custom_rate = fields.Float('Custom Rate', default=1.0, help="Set new currency rate to apply on the payment")
    currency_rate = fields.Float('Currency Rate',
                                 help="Technical field used to get acctual Currency Rate As 1/custom_rate",
                                 compute="_get_currency_rate")
    # field payment_date has been deprecated in 14 so we add it here
    payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, readonly=True,
                               states={'draft': [('readonly', False)]}, copy=False, tracking=True)

    @api.depends('custom_rate')
    def _get_currency_rate(self):
        """
        get acctual Currency Rate As 1/custom_rate
        """
        for rec in self:
            rec.currency_rate = 1 / rec.custom_rate

    def post(self):
        """Overrides post(), that Creates the journal items for the payment and
          update the payment's state to 'posted' with inclusion to custom rate
          to use in currency related calculations.
        """
        res = super(account_payment, self.with_context(custom_rate=self.custom_rate)).post()
        return res

    @api.onchange('currency_id', 'payment_date')
    def _onchange_currency_date(self):
        # Update custom rate value onchange of date value

        today = fields.Date.today()
        self.custom_rate = self.currency_id._get_conversion_rate(self.currency_id,self.company_id.currency_id,
                                                                 self.company_id, self.payment_date or today)



    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        res = super(account_payment, self.with_context(custom_rate=self.custom_rate))._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
        for rec in res:
            rec['custom_rate'] = self.custom_rate
        return res

    def _update_move_line_default_vals(self):
        if self.move_id:
           account_id = self.move_id.line_ids[0]
           account_id.update({'account_id':self.journal_id.default_account_id.id})  

             

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        print("\n\n\n\n\n\n\n\n")
        print("-----------_synchronize_to_moves-----------------")
        if 'journal_id' in changed_fields:
            self._update_move_line_default_vals()
        # if self._context.get('skip_account_move_synchronization'):
        #     return
        if not any(field_name in changed_fields for field_name in (
            'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
            'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'custom_rate','journal_id','check_type','payment_method_id',
        )):
            return
        for pay in self.with_context(skip_account_move_synchronization=True, custom_rate=self.custom_rate,journal_id=self.journal_id):
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.
            if writeoff_lines:
                print("***************************************",writeoff_lines)
                counterpart_amount = sum(
                    counterpart_lines.mapped('amount_currency'))
                writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

                # To be consistent with the payment_difference made in account.payment.register,
                # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                # Since the write is already done at this point, we need to base the computation on accounting values.
                if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                    sign = -1
                else:
                    sign = 1
                writeoff_amount = abs(writeoff_amount) * sign

                write_off_line_vals = {
                    'name': writeoff_lines[0].name,
                    'amount': writeoff_amount,
                    'account_id': writeoff_lines[0].account_id.id,
                }
            else:
                write_off_line_vals = {}

            line_vals_list = pay.with_context(custom_rate=pay.custom_rate)._prepare_move_line_default_vals(
                write_off_line_vals=write_off_line_vals)

            line_ids_commands = [
                (1, liquidity_lines.id, line_vals_list[0]),
                (1, counterpart_lines.id, line_vals_list[1]),
            ]

            print("\n\n\n\n\n\n\n")
            print("---------------------------writeoff_lines",writeoff_lines)
            for line in writeoff_lines:
                line_ids_commands.append((2, line.id))

            for extra_line_vals in line_vals_list[2:]:
                line_ids_commands.append((0, 0, extra_line_vals))

            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.

            print ("----------line_ids_commands",line_ids_commands)
            pay.move_id.write({
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands,
            })   

    # def _synchronize_to_moves(self, changed_fields):
    #     ''' Update the account.move regarding the modified account.payment.
    #     :param changed_fields: A list containing all modified fields on account.payment.
    #     '''
    #     if self._context.get('skip_account_move_synchronization'):
    #         return
    #     if not any(field_name in changed_fields for field_name in (
    #         'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
    #         'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'custom_rate', 
    #     )):
    #     # 'check_type','payment_method_id', 'journal_id'
    #         return
    #     for pay in self.with_context(skip_account_move_synchronization=True, custom_rate=self.custom_rate):
    #         liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

    #         # Make sure to preserve the write-off amount.
    #         # This allows to create a new payment with custom 'line_ids'.
    #         if writeoff_lines:
    #             counterpart_amount = sum(
    #                 counterpart_lines.mapped('amount_currency'))
    #             writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

    #             # To be consistent with the payment_difference made in account.payment.register,
    #             # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
    #             # Since the write is already done at this point, we need to base the computation on accounting values.
    #             if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
    #                 sign = -1
    #             else:
    #                 sign = 1
    #             writeoff_amount = abs(writeoff_amount) * sign

    #             write_off_line_vals = {
    #                 'name': writeoff_lines[0].name,
    #                 'amount': writeoff_amount,
    #                 'account_id': writeoff_lines[0].account_id.id,
    #             }
    #         else:
    #             write_off_line_vals = {}

    #         line_vals_list = pay.with_context(custom_rate=pay.custom_rate)._prepare_move_line_default_vals(
    #             write_off_line_vals=write_off_line_vals)

    #         line_ids_commands = [
    #             (1, liquidity_lines.id, line_vals_list[0]),
    #             (1, counterpart_lines.id, line_vals_list[1]),
    #         ]
    #         print("\n\n\n\n\n")
    #         print("++++++++++++++++++++++++++++++++",line_ids_commands)

    #         for line in writeoff_lines:
    #             line_ids_commands.append((2, line.id))

    #         for extra_line_vals in line_vals_list[2:]:
    #             line_ids_commands.append((0, 0, extra_line_vals))

    #         # Update the existing journal items.
    #         # If dealing with multiple write-off lines, they are dropped and a new one is generated.
    #         print("\n\n\n\n\n222222",writeoff_lines, line_vals_list[2:])
    #         print("++++++++++++++++++++++++++++++++222222",line_ids_commands)
    #         pay.move_id.write({
    #             'partner_id': pay.partner_id.id,
    #             'currency_id': pay.currency_id.id,
    #             # 'journal_id':pay.journal_id.id,
    #             'partner_bank_id': pay.partner_bank_id.id,
    #             'line_ids': line_ids_commands,
    #         })

# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    loan_payment_id = fields.Many2one("loan.payment", string="Loan Payment", required=False, )

    def action_post(self):
        rec = super(AccountMove, self).action_post()
        payment_line = self.env['loan.payment'].search(
            [('id', '=', self.loan_payment_id.id)])
        if payment_line:
            payment_line.write({'state': 'paid'})
            for line in payment_line.loan_line_ids:
                line.action_paid_amount()
        return rec

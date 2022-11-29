# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError
import time
from datetime import date, datetime


class ChequeWizard(models.TransientModel):
    _name = 'cheque.wizard'

    date_from = fields.Date(string="From",required=True)
    date_to = fields.Date(string="To",required=True)
    # customer_id = fields.Many2many('res.partner',string="Customer")
    customer_id = fields.Many2many('res.partner','rel_partner','customer_id','user_id',string="Customer")
    # under_collection = fields.Boolean(string="Under Collection")
    # in_bank = fields.Boolean(string="In Bank")
    # rejected = fields.Boolean(string="Check Rejected")
    # return_to = fields.Boolean(string="Return to Partner")
    # out_standing = fields.Boolean(string="Out Standing")
    # withdrawal = fields.Boolean(string="Withdraw From Bank")
    # done = fields.Boolean(string="Done")
    # cancel = fields.Boolean(string="Canceled")

    state = fields.Selection([
        ('under_collection', 'Under Collection'),
        ('in_bank', 'In Bank'),
        ('rdc', 'Check Rejected'),
        ('return_acc', 'Return to Partner'),
        ('donec', 'Done'),
        ('out_standing', 'Out Standing'),
        ('withdrawal', 'Withdraw From Bank'),
        ('rdv', 'Check Rejected'),
        ('return_acv', 'Return to Partner'),
        ('donev', 'Done'),
        ('cancel', 'Canceled')],string="State")

    # company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)


    def print_report(self):
        
        data = {
            'ids': self.ids,
            'model': self._name,
            'date_from': fields.Date.from_string(self.date_from),
            'date_to': fields.Date.from_string(self.date_to),
            'customer_id': self.customer_id.id,
            'customer_name': self.customer_id.name,
            # 'under_collection':  self.under_collection,
            # 'in_bank' : self.in_bank,
            # 'rejected' : self.rejected,
            # 'out_standing':  self.out_standing,
            # 'return_to' : self.return_to,
            # 'withdrawal': self.withdrawal,
            # 'done': self.done,
            # 'cancel' :self.cancel,
            'state': self.state,
            # 'company_id' : self.company_id.id, 
            }
        # data = {}

        print("******************************8888",self.date_from,self.customer_id)
        # data['date_from'] = self.date_from
        # data['date_to'] = self.date_to
        # date['customer'] = self.customer_id.id
        # date['under_collection'] = self.under_collection
        # date['in_bank'] = self.in_bank
        # date['rejected'] = self.rejected
        # date['out_standing'] = self.out_standing
        # date['withdrawal'] = self.withdrawal
        # date['done'] = self.done
        # date['cancel'] = self.cancel
        # data['comp'] = self.company_id.id

        return self.env.ref('zaway_account_custom.cheque_report_id').report_action([], data=data)

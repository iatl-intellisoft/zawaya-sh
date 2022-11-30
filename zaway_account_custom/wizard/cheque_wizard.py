# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError
import time
from datetime import date, datetime


class ChequeWizard(models.TransientModel):
    _name = 'cheque.wizard'

    date_from = fields.Date(string="From",required=True)
    date_to = fields.Date(string="To",required=True)
    customer_id = fields.Many2many('res.partner','rel_partner','customer_id','user_id',string="Customer")

    state = fields.Selection([
        ('under_collection', 'Under Collection'),
        ('in_bank', 'In Bank'),
        ('reject', 'Check Rejected'),
        ('return', 'Return to Partner'),
        ('done', 'Done'),
        ('out_standing', 'Out Standing'),
        ('withdrawal', 'Withdraw From Bank'),
        ('cancel', 'Canceled')],string="State")

    # company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)


    def print_report(self):
        
        data = {
            'ids': self.ids,
            'model': self._name,
            'date_from': fields.Date.from_string(self.date_from),
            'date_to': fields.Date.from_string(self.date_to),
            'customer_id': self.customer_id.ids,
            'state': self.state,
            }

        return self.env.ref('zaway_account_custom.cheque_report_id').report_action([], data=data)

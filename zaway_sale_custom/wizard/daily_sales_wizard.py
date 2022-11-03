# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError
import time
from datetime import date, datetime


class DailySalesWizard(models.TransientModel):
    _name = 'daily.sales.wizard'

    date_from = fields.Date(string="تاريخ من",required=True)
    date_to = fields.Date(string="إلي",required=True)
    company_id = fields.Many2one('res.company', string="الشركة", default=lambda self: self.env.user.company_id)


    def print_report(self):
        data = {}

        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        data['comp'] = self.company_id.id

        return self.env.ref('zaway_sale_custom.daily_sales_report_id').report_action([], data=data)

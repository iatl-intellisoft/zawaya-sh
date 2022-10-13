# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError
import time
from datetime import date, datetime


class ProductionWizard(models.TransientModel):
    _name = 'production.wizard'

    date_from = fields.Date(string="التاريخ",required=True)
    equipment_id = fields.Many2one('maintenance.equipment', string="ماكينة")
    company_id = fields.Many2one('res.company', string="الشركة", default=lambda self: self.env.user.company_id)


    def print_report(self):
        data = {}

        data['date_from'] = self.date_from
        data['equipment_id'] = self.equipment_id.id
        data['equipment_name'] = self.equipment_id.name
        data['comp'] = self.company_id.id

        return self.env.ref('zaway_maintenance_custom.production_report_id').report_action([], data=data)

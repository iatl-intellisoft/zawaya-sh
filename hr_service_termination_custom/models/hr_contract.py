# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HRContractCustom(models.Model):
    _inherit = 'hr.contract'


    remaining_days = fields.Float(srting="Annaul Remaining days",compute='_compute_remaining_days')

    def _compute_remaining_days(self):
        for rec in self:
            # remaining_days = 0.0
            # leave_type_ids = self.env['hr.leave.type'].search([('in_term_payslip','=',True)])
            # for leave in leave_type_ids:
            #     result = leave.get_employees_days(rec.employee_id.ids)
            #     leave_days = result[rec.employee_id.id][leave.id]
            #     if leave_days.get('remaining_leaves'):
            #         remaining_days+=leave_days['remaining_leaves']
            rec.remaining_days = rec.employee_id.annual_remaining_days
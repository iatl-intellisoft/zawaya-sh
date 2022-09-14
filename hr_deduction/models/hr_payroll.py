# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import api, fields, models

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=False)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_total_deduction(self):
        """
        A method to compute total deduction amount
        """
        total = 0.00
        for line in self.deduct_ids:
            total += line.de_amount
        self.total_deduct_amount = total

    deduct_ids = fields.Many2many('hr.deduction', 'hr_deduction_payslip_rel', 'deduct_ids', 'payslip_id', string='Deductions')
    total_deduct_amount = fields.Float(string="Total Deduction Amount", compute='compute_total_deduction')

    def get_deduction(self):
        """
        A method to get deduction
        """
        for rec in self:
            rec.deduct_ids = self.env['hr.deduction'].search([('employee_id', '=', rec.employee_id.id),
                                                              ('state', '=', 'approve'),
                                                              ('start_date', '>=', rec.date_from),
                                                              ('end_date', '<=', rec.date_to)
                                                              ]).ids

    def compute_sheet(self):
        self.get_deduction()
        return super(HrPayslip, self.sudo()).compute_sheet()

    def action_payslip_cancel(self):
        """
        A method to cancel payslip deduction
        """
        res = super(HrPayslip, self).action_payslip_cancel()
        for rec in self:
            rec.deduct_ids.write({'payslip_id': False})
        return res

    def unlink(self):
        self.deduct_ids = False
        return super(HrPayslip, self).unlink()  
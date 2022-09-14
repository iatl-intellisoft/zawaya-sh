# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import api, fields, models

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_total_incentive(self):
        """
        A method to compute total incentive amount
        """
        total = 0.00
        for line in self.incentive_ids:
            total += line.amount
        self.total_incentive_amount = total

    incentive_ids = fields.Many2many('hr.incentive.line', 'hr_incentive_line_payslip_rel', 'incentive_ids', 'payslip_id', string='Employee Payments')
    total_incentive_amount = fields.Float(string="Total Payment Amount", compute='compute_total_incentive')

    def _get_incentive(self):
        """
        A method to get incentive records
        """
        for rec in self:
            rec.incentive_ids = self.env['hr.incentive.line'].search([('employee_id', '=', rec.employee_id.id),
                                                                    ('incentive_id.incentive_type_id.payroll', '=' ,True), 
                                                                    ('incentive_id.state', '=', 'approved'),
                                                                    ('incentive_id.date', '>=', rec.date_from),
                                                                    ('incentive_id.end_date', '<=', rec.date_to),
                                                                    ('paid','=',False)
                                                                    ]).ids

    def compute_sheet(self):
        self._get_incentive()
        return super(HrPayslip, self.sudo()).compute_sheet()

    def action_update_related_records(self):
        """
        overwrite to update incentive records
        """
        res = super(HrPayslip, self).action_update_related_records()
        for rec in self:
            rec.incentive_ids.action_paid_amount()
        return res

    def action_payslip_cancel(self):
        """
        A method to cancel payslip incentive
        """
        for rec in self:
            rec.incentive_ids.write({'payslip_id': False, 'paid': False})
        return super(HrPayslip, self).action_payslip_cancel()

    def unlink(self):
        self.incentive_ids = False
        return super(HrPayslip, self).unlink()    
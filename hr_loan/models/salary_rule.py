# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models

class HRSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    use_type = fields.Selection(selection_add=[('loan', 'Loan')])
    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=False)


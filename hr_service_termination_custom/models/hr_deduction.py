# -*- coding: utf-8 -*-

from odoo import models, fields


class HRDeduction(models.Model):
    _inherit = 'hr.deduction'

    in_term_payslip = fields.Boolean(string="Included in Service Termination Payslip", default=False)

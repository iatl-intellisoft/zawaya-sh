# -*- coding: utf-8 -*-

from odoo import models, fields


class HRIncentive(models.Model):
    _inherit = 'hr.incentive'

    in_term_payslip = fields.Boolean(string="Included in service termination payslip", default=False)

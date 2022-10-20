# -*- coding: utf-8 -*-

from odoo import models, fields


class HrLoanLine(models.Model):
    _inherit = 'hr.loan.line'

    termination_id = fields.Many2one("hr.service.termination", string="Service Termination")

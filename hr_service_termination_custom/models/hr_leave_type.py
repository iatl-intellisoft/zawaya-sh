# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError



class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    in_term_payslip = fields.Boolean(string="Included in service termination payslip", default=False)
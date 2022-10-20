# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import models, fields, api

class TerminationReasons(models.Model):
    _name = 'hr.service.termination.reasons'

    name = fields.Char(required=True)
    rule_ids = fields.Many2many('hr.salary.rule', string='Salary Rules', domain=[('use_type', '=', 'termination')])

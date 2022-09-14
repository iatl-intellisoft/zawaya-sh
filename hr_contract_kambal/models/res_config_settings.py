# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models

class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_contract_template_id = fields.Many2one('mail.template', string='Employee Contract Template',
                                               related='company_id.employee_contract_template_id', readonly=False)

class ResCompany(models.Model):
    _inherit = 'res.company'

    employee_contract_template_id = fields.Many2one('mail.template', string='Employee Contract Template',
                                               domain="[('model','=','hr.contract')]")
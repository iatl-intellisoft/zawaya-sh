# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import api, fields, models, _

class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    service_termination_template_id = fields.Many2one('mail.template',
                                                      domain="[('model','=','hr.service.termination')]",
                                                      string='Service Termination  Template',
                                                      related='company_id.service_termination_template_id',
                                                      readonly=False)
    service_termination_clearance_ids = fields.Many2many('hr.department', string='Clearance Department', readonly=False,
                                                         related='company_id.service_termination_clearance_ids')
    service_termination_strcut_id = fields.Many2one('hr.payroll.structure', string='Termination Structure',
                                                    related='company_id.service_termination_strcut_id', readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    service_termination_template_id = fields.Many2one('mail.template', string='Service Termination Template',
                                                      domain="[('model','=','hr.service.termination')]")
    service_termination_clearance_ids = fields.Many2many('hr.department', string='Clearance Department')
    service_termination_strcut_id = fields.Many2one('hr.payroll.structure', 'Termination Structure', readonly=False)

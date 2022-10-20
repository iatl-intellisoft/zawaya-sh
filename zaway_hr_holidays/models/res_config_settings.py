

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

	leave_clearance_ids = fields.Many2many('hr.department', string='Clearance Department', readonly=False,
														 related='company_id.leave_clearance_ids')
	leave_certificate_template_id = fields.Many2one('mail.template', string='Time Off Certificate Template',
											   related='company_id.leave_certificate_template_id', readonly=False)
	sick_template_id = fields.Many2one('mail.template', string='Sick Time Off Template',
											   related='company_id.sick_template_id', readonly=False)
	salary_expences_account_id = fields.Many2one('account.account', string='Salary/Expenses Account', related='company_id.salary_expences_account_id',
                                          readonly=False)

class ResCompany(models.Model):
	_inherit = 'res.company'

	leave_clearance_ids = fields.Many2many('hr.department', 'company_rel_leave_clearance',string='Clearance Department')
	leave_certificate_template_id = fields.Many2one('mail.template', string='Time Off Certificate Template',
											   domain="[('model','=','hr.leave')]")
	sick_template_id = fields.Many2one('mail.template', string='Sick Time Off Template',
											   domain="[('model','=','hr.leave')]")
	salary_expences_account_id = fields.Many2one('account.account', string='Salary/Expenses Account',
												)

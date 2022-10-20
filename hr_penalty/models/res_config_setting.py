# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models

class ResConfigSetting(models.TransientModel):
	_inherit = 'res.config.settings'
	
	penalty_template_id = fields.Many2one('mail.template',related='company_id.penalty_template_id',string='Penalty Template',readonly=False,domain=lambda self:[('model_id','=',self.env.ref('hr_penalty.model_hr_penalty').id)],store=True)

class resCompany(models.Model):
	_inherit = "res.company"

	penalty_template_id = fields.Many2one('mail.template',string='Penalty Template')



	
	
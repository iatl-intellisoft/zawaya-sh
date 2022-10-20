# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models

class Company(models.Model):
    _inherit = 'res.company'
    labor_account_id = fields.Many2one('account.account', string='account')
    analytic_account_id = fields.Many2one('account.analytic.account', 'analytic account')
    detailed_payment = fields.Boolean(string="Detailed Payment")

class TemporaryServiceConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    labor_account_id = fields.Many2one('account.account', string='account', related='company_id.labor_account_id', readonly=False)
    analytic_account_id = fields.Many2one('account.analytic.account', string='analytic account',
                                          related='company_id.analytic_account_id', readonly=False)
    detailed_payment = fields.Boolean(string="Detailed Payment", related='company_id.detailed_payment', readonly=False)

class Partner(models.Model):
    _inherit = 'res.partner'

    labor = fields.Boolean(string="Labor")

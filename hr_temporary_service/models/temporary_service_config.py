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
    temporary_ser_debit_account_id = fields.Many2one('account.account', string='Dedit Account')
    temporary_ser_credit_account_id = fields.Many2one('account.account', string='Credit Account')
    temporary_service_journal_id = fields.Many2one('account.journal', string='Journal')
    # analytic_account_id = fields.Many2one('account.analytic.account', 'analytic account')
    detailed_payment = fields.Boolean(string="Detailed Payment")
    tem_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')


class TemporaryServiceConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    labor_account_id = fields.Many2one('account.account', string='account', related='company_id.labor_account_id',
                                       readonly=False)
    tem_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                              related='company_id.tem_account_analytic_id', readonly=False)
    # analytic_account_id = fields.Many2one('account.analytic.account', string='analytic account',
    #                                       related='company_id.analytic_account_id', readonly=False)
    detailed_payment = fields.Boolean(string="Detailed Payment", related='company_id.detailed_payment', readonly=False)
    # temporary_service_account_id temporary_service_journal_id

    temporary_ser_credit_account_id = fields.Many2one('account.account', string='Credit Account', related='company_id.temporary_ser_credit_account_id',readonly=False)
    temporary_ser_debit_account_id = fields.Many2one('account.account', string='Dedit Account', related='company_id.temporary_ser_debit_account_id',readonly=False)
    temporary_service_journal_id = fields.Many2one('account.journal', string='Journal', related='company_id.temporary_service_journal_id',readonly=False)


class Partner(models.Model):
    _inherit = 'res.partner'
    labor = fields.Boolean(string="Labor")


class Departments(models.Model):
    _inherit = 'hr.department'

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
class AccountMove(models.Model):
    _inherit = 'account.move'

    temporary_service_id = fields.Many2one("hr.temporary.service", string="Temporary Service")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tem_service_line_id = fields.Many2one("temporary.service.line", string="Temporary Service Line")


# -*- coding: utf-8 -*-
###################################################################################
#    Copyright (C) 2020-Today IATL IntelliSoft (<http://www.iatl-intellisoft.com>)#
###################################################################################

import copy
import ast

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, ustr
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.addons.account_reports.models.formula import FormulaLocals


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"
    
    def _default_usd_currency(self):
        return self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

    currency_usd = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,default=_default_usd_currency)
    @api.model
    def _format_cell_value(self, financial_line, amount, currency=False, blank_if_zero=False):
        if 'USD' in self.name:
            return super().format_value(amount, currency=self.currency_usd, blank_if_zero=blank_if_zero)
        else:
            return super()._format_cell_value(financial_line,amount,currency,blank_if_zero)



class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"


    us_rate = fields.Float('US Rate',default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')], limit=1).rate)
    us_formulas = fields.Char()
    def _copy_hierarchy(self, report_id=None, copied_report_id=None, parent_id=None, code_mapping=None):
        ''' Copy the whole hierarchy from this line by copying each line children recursively and adapting the
        formulas with the new copied codes.

        :param report_id: The financial report that triggered the duplicate.
        :param copied_report_id: The copy of old_report_id.
        :param parent_id: The parent line in the hierarchy (a copy of the original parent line).
        :param code_mapping: A dictionary keeping track of mapping old_code -> new_code
        '''
        self.ensure_one()
        if code_mapping is None:
            code_mapping = {}
        # If the line points to the old report, replace with the new one.
        # Otherwise, cut the link to another financial report.
        if report_id and copied_report_id and self.financial_report_id.id == report_id.id:
            financial_report_id = copied_report_id.id
        else:
            financial_report_id = None
        copy_line_id = self.copy({
            'financial_report_id': financial_report_id,
            'parent_id': parent_id and parent_id.id,
            'code': self.code and self._get_copied_code(),
        })
        # Keep track of old_code -> new_code in a mutable dict
        if self.code:
            code_mapping[self.code] = copy_line_id.code
        # Copy children
        for line in self.children_ids:
            line._copy_hierarchy(parent_id=copy_line_id, code_mapping=code_mapping)
        # Update formulas
        if self.formulas:
            copied_formulas = self.formulas
            for k, v in code_mapping.items():
                for field in ('debit', 'credit', 'balance','amount_residual', 'us_debit', 'us_credit', 'us_balance',
                              'us_amount_residual'):
                    suffix = '.' + field
                    copied_formulas = copied_formulas.replace(k + suffix, v + suffix)
            copy_line_id.formulas = copied_formulas
            
    def _compute_amls_results(self, options_list, calling_financial_report, sign=1, operator=None):
        if 'USD' in self.name:
            self.ensure_one()
            params = []
            queries = []

            AccountFinancialReportHtml = self.financial_report_id
            horizontal_groupby_list = AccountFinancialReportHtml._get_options_groupby_fields(options_list[0])
            groupby_list = [self.groupby] + horizontal_groupby_list
            groupby_clause = ','.join('account_move_line.%s' % gb for gb in groupby_list)
            groupby_field = self.env['account.move.line']._fields[self.groupby]

            ct_query = self.env['res.currency']._get_query_currency_table(options_list[0])
            parent_financial_report = self._get_financial_report()

            # Prepare a query by period as the date is different for each comparison.

            for i, options in enumerate(options_list):
                new_options = self._get_options_financial_line(options, calling_financial_report,
                                                               parent_financial_report)
                line_domain = self._get_domain(new_options, parent_financial_report)

                tables, where_clause, where_params = AccountFinancialReportHtml._query_get(new_options,
                                                                                           domain=line_domain)

                queries.append('''
                            SELECT
                                ''' + (groupby_clause and '%s,' % groupby_clause) + '''
                                %s AS period_index,
                                COALESCE(SUM(ROUND(%s * account_move_line.us_balance * currency_table.rate, currency_table.precision)), 0.0) AS balance
                            FROM ''' + tables + '''
                            JOIN ''' + ct_query + ''' ON currency_table.company_id = account_move_line.company_id
                            WHERE ''' + where_clause + '''
                            ''' + (groupby_clause and 'GROUP BY %s' % groupby_clause) + '''
                        ''')
                params += [i, sign] + where_params

            # Fetch the results.
            # /!\ Take care of both vertical and horizontal group by clauses.

            results = {}

            self._cr.execute(' UNION ALL '.join(queries), params)
            for res in self._cr.dictfetchall():
                # Build the key.
                key = [res['period_index']]
                for gb in horizontal_groupby_list:
                    key.append(res[gb])
                key = tuple(key)

                results.setdefault(res[self.groupby], {})
                results[res[self.groupby]][key] = res['balance']

            # Sort the lines according to the vertical groupby and compute their display name.
            if groupby_field.relational:
                # Preserve the table order by using search instead of browse.
                sorted_records = self.env[groupby_field.comodel_name].search([('id', 'in', tuple(results.keys()))])
                sorted_values = sorted_records.name_get()
            else:
                # Sort the keys in a lexicographic order.
                sorted_values = [(v, v) for v in sorted(list(results.keys()))]

            return [(groupby_key, display_name, results[groupby_key]) for groupby_key, display_name in sorted_values]
        else:
            return super(AccountFinancialReportLine, self)._compute_amls_results(options_list, calling_financial_report, sign=sign)

class AccountAccount(models.Model):
    _inherit = 'account.account'
    us_appear = fields.Boolean(string='Remove from US P&L Report')

# inherit to add dollar rate as we require all transactions in dollars
class AccountMove(models.Model):
    _inherit = 'account.move'

    us_rate = fields.Float('US Rate', compute='compute_usd_rate')


    # @api.onchange('date')
    @api.depends('date','partner_id')
    def compute_usd_rate(self):
        for rec in self:
            rec.us_rate = 0.0
            if rec.date:
                rate =self.env['res.currency.rate'].search([('currency_id.name', '=', 'USD'), ('name', '=', rec.date)],
                                                     limit=1)
                if not rate:
                    rate = self.env['res.currency.rate'].search([('currency_id.name', '=', 'USD'), ('name', '<', rec.date)],
                                                                limit=1)
                # raise UserError(rate)
                rec.us_rate = rate.rate

########################################################################################################################
# inherit to add US debit and credit columns
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    us_debit = fields.Float(string='US Debit', default=0.0, readonly=True, compute='us_equivalent', store=True)
    us_credit = fields.Float(string='US Credit', default=0.0, readonly=True, compute='us_equivalent', store=True)
    us_balance = fields.Float(string='US Balance', store=True, readonly=True, compute='compute_us_balance')
    us_amount_residual = fields.Float(string='US Residual Amount', store=True, readonly=True,
                                         compute='us_equivalent')
    us_amount_currency = fields.Monetary(string='Amount in Currency', store=True, copy=True,compute='us_equivalent')
    us_rate = fields.Float('US Rate', compute='compute_usd_rate', store=True)

    @api.depends('date')
    def compute_usd_rate(self):
        for rec in self:
            rec.us_rate = 0.0
            rate = 0.0
            if rec.date:
                rate = self.env['res.currency.rate'].search([('currency_id.name', '=', 'USD'), ('name', '=', rec.date)],
                                                        limit=1).rate
                if not rate:
                    rate = self.env['res.currency.rate'].search(
                        [('currency_id.name', '=', 'USD'), ('name', '<', rec.date)],
                        limit=1).rate
                # raise UserError(rate)
                # if rate:
            rec.us_rate = rate

    @api.depends('debit', 'credit', 'amount_currency', 'currency_id', 'balance', 'amount_residual', 'account_id.us_appear')
    def us_equivalent(self):
        for rec in self:
            us_appear = rec.account_id.us_appear
            rec.us_debit = 0.0
            rec.us_credit = 0.0
            rec.us_amount_residual = 0.0
            rec.us_amount_currency = 0.0
            # get US equivalent immediately
            if not us_appear:
                if rec.debit > 0.0:
                    if rec.currency_id.name == 'USD':
                        rec.us_debit = rec.amount_currency
                    else:
                        rec.us_debit = rec.debit * rec.move_id.us_rate
                if rec.credit > 0.0:
                    if rec.currency_id.name == 'USD':
                        rec.us_credit = -rec.amount_currency
                    else:
                        rec.us_credit = rec.credit * rec.move_id.us_rate
                rec.us_amount_residual = rec.amount_residual * rec.move_id.us_rate
                rec.us_amount_currency = rec.amount_currency * rec.move_id.us_rate

    @api.depends('us_debit', 'us_debit', 'balance', 'currency_id', 'amount_currency', 'move_id.state')
    def compute_us_balance(self):
        for rec in self:
            rec.us_balance = rec.us_debit - rec.us_credit


class FormulaLocals1(FormulaLocals):
    ''' Class to set as "locals" when evaluating the formula to compute all formula.
    The evaluation must be done for each key so this class takes a key as parameter.
    '''


    def __getitem__(self, item):
        if item == 'NDays':
            return self.solver._get_number_of_days(self.key[0])
        elif item == 'from_context':
            return self.solver._get_balance_from_context(self.financial_line)
        elif item == 'count_rows':
            return self.solver._get_amls_results(self.financial_line)[item].get(self.key[0], 0)
        elif item in ('sum', 'sum_if_pos', 'sum_if_neg'):
            if self.financial_line.us_formulas:
                return self.solver._get_amls_results(self.financial_line)[item].get(self.key, 0.0) * self.financial_line.us_rate
            else:
                
                return self.solver._get_amls_results(self.financial_line)[item].get(self.key, 0.0)
        else:
            financial_line = self.solver._get_line_by_code(item)
            if not financial_line:
                return super().__getitem__(item)
            return self.solver._get_formula_results(financial_line).get(self.key, 0.0)

FormulaLocals.__getitem__ = FormulaLocals1.__getitem__


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def open_general_ledger(self, options, params=None):
        if 'USD' in self.name:
            if not params:
                params = {}
            ctx = self.env.context.copy()
            ctx.pop('id', '')
            ctx['default_filter_accounts'] = self.env['account.account'].browse(params.get('id', 0)).code or ''
            action = self.env["ir.actions.actions"]._for_xml_id("ii_accounting_us.action_account_report_general_ledger_usd")
            options['unfolded_lines'] = ['account_%s' % (params.get('id', ''),)]
            options['unfold_all'] = False
            if 'date' in options and options['date']['mode'] == 'single':
                # If we are coming from a report with a single date, we need to change the options to ranged
                options['date']['mode'] = 'range'
                options['date']['period_type'] = 'fiscalyear'
            ctx.update({'model': 'account.general.ledger.usd'})
            action.update({'params': {'options': options, 'context': ctx, 'ignore_session': 'read'}})
            return action
        else:
            return super().open_general_ledger(options, params=params)

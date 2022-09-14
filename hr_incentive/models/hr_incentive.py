# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools.translate import html_translate

class HrIncentiveType(models.Model):
    _name = 'hr.incentive.type'

    name = fields.Char('Name', required=True)
    rule_id = fields.Many2one('hr.salary.rule', string='Compute base on')
    account_id = fields.Many2one('account.account', string="Account",company_dependent=True)
    payroll = fields.Boolean(string="Through Payroll")
    type_in = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fix', 'Fixed Amount'),
        ('hours', 'Hours'), ], string='Payments By', default='fix',
    )
    journal_id = fields.Many2one('account.journal', string="Journal", domain=[('type', '=', 'purchase')],company_dependent=True)

class HrIncentive(models.Model):
    _name = 'hr.incentive'
    _description = 'HR Incentive'
    _order = "date desc, id desc"

    name = fields.Char(string='Number', readonly=True)
    request_id = fields.Many2one('res.users', string='Requestor', default=lambda self: self.env.user)
    date = fields.Date(string="Start Date", default=lambda self: fields.Date.context_today(self))
    end_date = fields.Date(string="End Date")
    approve_date = fields.Date(string="Approve Date")
    manager_id = fields.Many2one('hr.employee', string='Manager')
    types = fields.Selection([
        ('all_staff', 'All Staff'),
        ('employee', 'certain Employee'),
        ('selected', 'Selected Employees'), ], string='Staff Payments Scope', default='all_staff', readonly=True,
        required='1',
        states={'draft': [('readonly', False)]}, tracking=5, ondelete='restrict')
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True,
                                  states={'draft': [('readonly', False)]})
    employee_ids = fields.Many2many('hr.employee', string='Employees', readonly=True,
                                    states={'draft': [('readonly', False)]})
    type_in = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fix', 'Fixed Amount'),
        ('hours', 'Hours')], related='incentive_type_id.type_in', ondelete='restrict', string='Payments By',
        readonly=True)
    amountx = fields.Float(string="Amount", readonly=True, tracking=5,
                           states={'draft': [('readonly', False)]})
    percentage = fields.Float(string=" Percentage (%)", tracking=5)

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states={'draft': [(
        'readonly', False)], 'submit': [('readonly', False)]}, default=lambda self: self.env.company)
    incentive_type_id = fields.Many2one(
        'hr.incentive.type', string='Type', ondelete='cascade', required=True)
    state = fields.Selection([
        ('draft', 'Open'),
        ('submit', 'Submit'),
        ('approved', 'Approved'),
        ('reject', 'Reject'),
        ('cancel', 'Cancel'),
    ], string='State', readonly=True, default='draft', tracking=5)
    incentive_line = fields.One2many('hr.incentive.line', 'incentive_id', readonly=True,
                                     states={'draft': [('readonly', False)], 'submit': [('readonly', False)]},
                                     ondelete='cascade')
    reason = fields.Text(readonly=True,
                         states={'draft': [('readonly', False)]})
    move_id = fields.Many2many('account.move', string='Receipts', readonly=True,copy=False)
    active = fields.Boolean('active', default=True)
    incentive_website_description = fields.Html('Body Template', sanitize_attributes=False, translate=html_translate,
                                                compute="get_incentive_website_description")
    incentive_template_id = fields.Many2one('mail.template', string='Incentive Template',
                                            related='company_id.incentive_template_id',
                                            store=True
                                            )

    def action_get_move_ids(self):
        return {
            'name': _('Recipts'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_id.ids)],
        }

    @api.depends('incentive_template_id', 'incentive_template_id.body_html')
    def get_incentive_website_description(self):
        """
        A method to create incentive website description template
        """
        for rec in self:
            rec.incentive_website_description += rec.incentive_website_description
            if rec.incentive_template_id and rec.id:
                fields = ['body_html']
                template_values = rec.incentive_template_id.generate_email([rec.id], fields=fields)
                rec.incentive_website_description = template_values[rec.id].get('body_html')

    def action_draft(self):
        """
        A method to make incentive draft
        """
        self.state = 'draft'

    def action_submit(self):
        """
        A method to submit incentive
        """
        if self.incentive_line:
            if self.company_id.incentive_double_validation == 'two_step' and self.amountx > self.company_id.incentive_double_validation_amount:
                self.state = 'submit'
            else:
                self.action_approve()
        else:
            raise Warning(
                _('Please compute the incentive line by press compute button'))

    def action_approve(self):
        """
        A method to approve incentive
        """
        if self.incentive_type_id.payroll == False:
            self.bt_money_received()
        self.state = 'approved'
        self.approve_date = fields.Date.today()

    def compute_incentive_line(self):
        """
        A method to compute incentive
        """
        incentive_line_obj = self.env['hr.incentive.line']
        if self.type_in != 'hours':
            incentive_line_obj.search([('incentive_id', '=', self.id)]).unlink()
        if self.types == 'all_staff':
            employees = self.env['hr.employee'].search([('active', '=', True)])
        elif self.types == 'employee':
            employees = self.employee_id
        elif self.types == 'selected':
            employees = self.employee_ids
        percentage = self.percentage
        amountx = self.amountx
        if self.type_in != 'hours':
            for re in employees:
                percentage = self.percentage
                if self.type_in == 'percentage':

                    if not self.incentive_type_id.rule_id:
                        raise ValidationError(_("Please enter Salary Rule in incentive type"))

                    rule_res = self.incentive_type_id.rule_id.compute_rule_amount(re)
                    amount = rule_res * (percentage / 100)
                    amountx = 0
                elif self.type_in == 'fix':
                    amount = amountx
                    percentage = 0
                else:
                    amountx = 0
                    amount = 0
                    percentage = 0

                line_id = incentive_line_obj.create({
                    'incentive_id': self.id,
                    'type_in': self.type_in,
                    'amountx': amountx,
                    'percentage': percentage,
                    'incentive_type_id': self.incentive_type_id.id,
                    'amount': amount,
                    'date': self.date,
                    'incentive_state': self.state,
                    'reason': self.reason,
                    'employee_id': re.id,
                    'company_id': self.company_id.id,

                })
        else:
            res = [r['employee_id'][0] for r in self.incentive_line.read(['employee_id'])]
            for re in employees:
                if not self.incentive_type_id.rule_id:
                    raise ValidationError(_("Please enter Salary Rule in incentive type"))
                rule_res = self.incentive_type_id.rule_id.compute_rule_amount(re)
                if re.id not in res:
                    line_id = incentive_line_obj.create({
                        'incentive_id': self.id,
                        # 'wage': re.contract_id.wage,
                        'type_in': self.type_in,
                        'amountx': 0,
                        'percentage': 0,
                        'incentive_type_id': self.incentive_type_id.id,
                        'amount': 0,
                        'date': self.date,
                        'incentive_state': self.state,
                        'reason': self.reason,
                        'employee_id': re.id,
                    })
            for line in self.incentive_line:
                if line.employee_id.id not in employees.ids:
                    line.unlink()
                else:
                    line.amount = rule_res * line.hours
        return True

    def bt_money_received(self):
        result = self.env['hr.incentive.line'].read_group([('incentive_id', '=', self.id)], ['bank_id'], ['bank_id'])
        for rec in result:
            recipt_lines = []
            lines = self.env['hr.incentive.line'].search(rec['__domain'])
            for line in lines:
                name = self.name or " "
                recipt_lines.append((0,0,{
                    'name': name + ' of ' + line.employee_id.name,
                    'account_id': self.incentive_type_id.account_id.id,
                    'price_unit': line.amount,
                    'partner_id': line.employee_id.address_home_id.id,
                    'quantity': 1,
                    'exclude_from_invoice_tab': False,
                }))
            bank =_("No Bank")
            if rec['bank_id']:
                bank = self.env['res.bank'].browse(rec['bank_id'][0]).name
            journal_id = self.incentive_type_id.journal_id
            vals = {
                'name': '/',
                # 'bank_id':rec['bank_id'] and rec['bank_id'][0] or False,
                'ref':'Staff Payment of ' + bank,
                'invoice_origin':self.name,
                'company_id': self.company_id.id,
                'partner_id':self.company_id.partner_id.id,
                'journal_id': journal_id.id,
                'move_type': 'in_receipt',
                # 'hr_receipt': True,
                'invoice_line_ids':recipt_lines,
            }
            move_id = self.env['account.move'].sudo().create(vals)
            self.move_id += move_id

    def action_reject(self):
        """
        A method to reject incentive
        """
        self.state = 'reject'

    def action_cancel(self):
        """
        A method to cancel incentive
        """
        for rec in self:
            if rec.move_id:
                if all(rec.mapped('move_id').filtered(lambda x:x.state == 'draft')):
                    rec.state = 'cancel'
                    rec.move_id.button_cancel()
                elif any(rec.mapped('move_id').filtered(lambda x:x.state == 'posted')):
                    raise ValidationError(_("There is a voucher linked with this record must be canceled first in order to cancel the record."))
                elif all(rec.mapped('move_id').filtered(lambda x:x.state == 'cancel')):
                    rec.state = 'cancel'
                else:
                    raise ValidationError(
                        _("You Shoud Cancel Or Delete The Recipts linked to this record first!"))
            elif rec.incentive_line.filtered('payslip_id'):
                raise ValidationError(_("Sorry! you can't cancel this record; There is a payslip /s for this record!"))
            rec.state = 'cancel'

    @api.model
    def create(self, vals):
        """
        A method to create incentive sequence
        """
        res = super(HrIncentive, self).create(vals)
        res.name = self.env['ir.sequence'].get('hr.incentive')
        return res

    def unlink(self):
        """
        A method to delete incentive
        """
        for incentive in self:
            if incentive.state not in ('draft', 'cancel'):
                raise Warning(
                    _('You can not delete an incentive which is not draft or cancelled.'))
        return super(HrIncentive, self).unlink()


class HRIncentiveLine(models.Model):
    _name = 'hr.incentive.line'
    _rec_name = 'employee_id'
    _order = 'date desc, department_id, amount desc'

    incentive_id = fields.Many2one(
        'hr.incentive', string='Staff Payments', readonly=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee',
                                  string='Employee', required=True)
    job_id = fields.Many2one('hr.job', string='Job Title',
                             compute='_get_employee', store=True, readonly=True)
    department_id = fields.Many2one(
        'hr.department', string=' Department', compute='_get_employee', store=True, readonly=True)
    type_in = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fix', 'Fixed Amount'),
        ('hours', 'Hours')],
        related='incentive_id.type_in', string='Payments By', invisible=True, readonly=True, ondelete='restrict')
    amountx = fields.Float(string="Amount")
    percentage = fields.Float(string=" Percentage (%)")
    hours = fields.Float(string="Hours")
    incentive_type_id = fields.Many2one('hr.incentive.type', related='incentive_id.incentive_type_id', string='Type',
                                        ondelete='restrict', invisible='1')
    amount = fields.Float(digits=dp.get_precision(
        'Payroll'), string='Payment amount', required=True)
    date = fields.Date(related='incentive_id.date')
    approve_date = fields.Date(related='incentive_id.approve_date')
    incentive_state = fields.Selection(
        related='incentive_id.state', string='Status', store=True, default='draft', readonly=True)
    reason = fields.Text(related='incentive_id.reason')
    payslip_id = fields.Many2many('hr.payslip', 'hr_incentive_line_payslip_rel', 'payslip_id', 'incentive_ids', string='Payslips')
    paid = fields.Boolean(string="Paid")
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    bank_id = fields.Many2one('res.bank',string='Employee Bank', compute='_get_employee_bank',store=True)

    @api.depends('employee_id')
    def _get_employee_bank(self):
        """
        A method to change bank to employee bank
        """
        for record in self:
            record.bank_id = record.employee_id.bank_account_id.bank_id

    def action_paid_amount(self):
        """
        A method to make amount in paid state
        """
        self.write({'paid': True})
        return True

    @api.depends('employee_id')
    def _get_employee(self):
        """
        A method to change job to employee job and department to employee department
        """
        for record in self:
            record.job_id = record.employee_id.job_id.id
            record.department_id = record.employee_id.department_id.id

    @api.onchange('hours')
    def _onchange_hours(self):
        """
        A method to compute incentive amount per hours
        """
        res = self.incentive_type_id.rule_id.compute_rule_amount(self.employee_id)
        amount = 0.0
        if self.type_in == 'hours' and self.hours:
            amount = (res * self.hours)
        self.amount = amount

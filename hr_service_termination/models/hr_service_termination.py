# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import models, fields, api, _
from datetime import datetime, time, timedelta
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import html_translate

class HrServiceTermination(models.Model):
    _name = 'hr.service.termination'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Termination Name", default="/", readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_join = fields.Date('Date of Join', related='employee_id.contract_id.date_start')
    department_id = fields.Many2one('hr.department', string='Department', readonly=True,
                                    related='employee_id.department_id', store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', readonly=True)
    reason_id = fields.Many2one('hr.service.termination.reasons', string='Termination Reason', required=True)
    termination_date = fields.Date('Termination Date', default=fields.date.today(), required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submit'), ('waiting_calculation', 'waiting service termination calculation'),
         ('done', 'Done'), ('cancel', 'Cancel')], default='draft')
    working_days = fields.Integer(string='Working Days', default=30, required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', related='employee_id.contract_id', readonly=True)
    move_id = fields.Many2one('account.move', string='Voucher')
    payslip_ids = fields.One2many('hr.payslip', 'termination_id')
    other_deduction = fields.Float('Other Deduction')
    other_allowances = fields.Float('Other Allowances')
    notice_month = fields.Boolean('Pay For Notice Month?')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    service_termination_website_description = fields.Html('Body Template', sanitize_attributes=False,
                                                          translate=html_translate, compute="get_termination_template")
    service_termination_template_id = fields.Many2one('mail.template', string='Service Termination Template',
                                                      related='company_id.service_termination_template_id', store=True)
    service_termination_clearance_ids = fields.One2many('service.termination.clearance.line', 'service_termination_id',
                                                        string='Clearance Department', )
    active = fields.Boolean(default=True)
    mail_track = fields.Many2one('mail.message', string="Mail tracking")

    def action_approve(self):
        """
        A method to approve service termination
        """
        company = self.env['res.company'].search([('id', '=', self.env.company.id)])
        termination_struct_id = company.service_termination_strcut_id
        if not termination_struct_id:
            raise UserError(_("Please enter service termination structure in Settings"))
        for rec in self:
            rec.employee_id.contract_id.write({'state': 'service_termination'})
            payslip_vals = {
                'name': _('Service Termination Slip of %s ') % (rec.employee_id.name),
                'employee_id': rec.employee_id.id,
                'contract_id': rec.employee_id.contract_id.id,
                'struct_id': termination_struct_id.id,
                'type': 'service_termination',
                'termination_id': self.id}
            payslip = self.env['hr.payslip'].create(payslip_vals)
            payslip.sudo().compute_sheet()
            rec.write({'state': 'waiting_calculation'})

    def action_submit(self):
        """
        A method to submit service termination and create clearance lines
        """
        for rec in self:
            rec.write({'state': 'submit'})

    def action_cancel(self):
        self.write({'state':'cancel'})  


    def action_draft(self):
        self.write({'state':'draft'})          

    def action_done(self):
        """
        A method to set service termination done.
        """
        for rec in self:

            lines = []

            for slip in rec.payslip_ids:
                lines = []
                for line in slip.line_ids:
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id
                    if debit_account_id:
                        debit_line = (0, 0, {
                            'name': line.salary_rule_id.name,
                            'partner_id': rec.employee_id.address_home_id.id,
                            'account_id': debit_account_id,
                            'price_unit': abs(line.total),
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                            'tax_line_id': line.salary_rule_id.account_tax_id.id,
                        })
                        lines.append(debit_line)
                    if credit_account_id:
                        credit_line = (0, 0, {
                            'name': line.salary_rule_id.name,
                            'partner_id': rec.employee_id.address_home_id.id,
                            'account_id': credit_account_id,
                            'price_unit': -abs(line.total),
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                            'tax_line_id': line.salary_rule_id.account_tax_id.id
                        })
                        lines.append(credit_line)
            vals = {
                'narration': 'Payslip voucher for service termination ' + rec.name,
                'ref': '/',
                'move_type': 'in_receipt',
                'hr_receipt': True,
                'line_ids': lines
            }
            rec.move_id = (self.env['account.move'].create(vals)).id
            rec.write({'state': 'done'})
            rec.employee_id.contract_id.write(
                {'date_end': rec.termination_date + timedelta(days=rec.working_days), 'state': 'terminated'})
            rec.employee_id.job_id.write({'employee_ids': [(3, rec.employee_id.id)]})

    def go_to_payslip(self):
        """
        A method read specific record from payslip.
        """
        self.ensure_one()
        action = self.env.ref('hr_payroll.action_view_hr_payslip_form')
        result = action.read()[0]
        result['domain'] = [('termination_id', '=', self.id)]
        return result

    @api.model
    def create(self, values):
        """
        A method to create service termination sequence.
        """
        values['name'] = self.env['ir.sequence'].get('hr.service.termination') or ' '
        record_id = super(HrServiceTermination, self).create(values)
        company = self.env['res.company'].search([('id', '=', self.env.company.id)])
        service_termination = self.search([('id', '=', record_id.id)])
        for department in company.service_termination_clearance_ids:
            service_termination.write({'service_termination_clearance_ids': [
                (0, 0, {'service_termination_id': record_id.id, 'department_id': department.id})]})
            # create mail activity for eacth department manager
            if not department.manager_id.id:
                raise UserError(_("Please Add Manager To %s Department") % (department.name))
            if not department.manager_id.user_id.id:
                raise UserError(_("Please Add User To %s ") % (department.manager_id.name))
            activity = self.env['mail.activity'].create({
                'note': "Please Approve " + str(record_id.employee_id.name) + " Clearance",
                'summary': 'Employee Clearance Approval',
                'res_id': record_id.id,
                'user_id': department.manager_id.user_id.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.service.termination')], limit=1).id,
            })
        return record_id

    @api.depends('service_termination_template_id', 'service_termination_template_id.body_html')
    def get_termination_template(self):
        """
        A method to get service termination template.
        """
        for rec in self:
            rec.service_termination_website_description += rec.service_termination_website_description
            if rec.service_termination_template_id and rec.id:
                fields = ['body_html']
                template_values = rec.service_termination_template_id.generate_email([rec.id], fields=fields)
                rec.service_termination_website_description = template_values[rec.id].get('body_html')

    def unlink(self):
        """
        A method to delete service termination record in draft state only.
        """
        for order in self:
            if order.state not in ('draft',):
                raise UserError(_('You can not delete record not in draft state.'))
        return super(HrServiceTermination, self).unlink()

class ServiceTerminationClearanceLine(models.Model):
    _name = 'service.termination.clearance.line'

    department_id = fields.Many2one('hr.department', string='Department', required=True)
    cleared = fields.Boolean('Cleared', readonly=True)
    notes = fields.Text('Notes')
    approve_by = fields.Many2one('hr.employee', string='Approve By')
    service_termination_id = fields.Many2one('hr.service.termination', string='Service Termination')

    def set_approve(self):
        """
        A method to approve service termination clearance records.
        """
        # current employee
        employee_obj = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

        if self.department_id.manager_id.id != employee_obj.id:
            raise UserError(_("Only %s manager can approve this clearance") % (self.department_id.name))

        self.approve_by = employee_obj.id
        self.cleared = True

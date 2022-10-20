# -*- coding: utf-8 -*-
from dateutil import relativedelta
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, time, timedelta

class HrServiceTermination(models.Model):
    _inherit = 'hr.service.termination'

    installments_ids = fields.One2many("hr.loan.line", "termination_id", string="Employee loans installments")

    loans_amount = fields.Float('Loans Amount', compute='compute_running_loans', default=0.0)
    deductions_amount = fields.Float('Deductions Amount', compute='compute_running_deductions', default=0.0)
    # incentives_amount = fields.Float('Incentives Amount', compute='compute_running_incentives', default=0.0)
    financial_data = fields.One2many('financial.data','fina_termina',string="Financial Data")
    remaining_days = fields.Float(srting="Leave Remaining days",related='employee_id.contract_id.remaining_days')
    last_joining_date = fields.Date(string='Last working day date', required=True,states={'draft': [('readonly', False)]})
    working_days = fields.Integer(string='Working Days',readonly=True, required=True,compute='_compute_working_days')
    custody_clear_id = fields.Many2one('custody.return',string="Custody Clearance No.",required=True)
    has_custody = fields.Boolean(compute="check_has_custody")

    @api.onchange('employee_id','termination_date')
    def clear_links(self):
        for installment in self.installments_ids:
            installment.write({'termination_id':False})

    def action_cancel(self):
        """
        """
        res = super(HrServiceTermination, self).action_cancel()
        self.clear_links()
        self.compute_running_deductions()
        # self.compute_running_incentives()

    @api.depends('employee_id')
    def check_has_custody(self):
        for line in self:
            line.has_custody = False
            request_no = self.env['custody.request'].search_count([('employee_id', '=', line.employee_id.id)])
            if  request_no > 0:
                line.has_custody = True
        
    @api.depends('employee_id','installments_ids')
    def compute_running_loans(self):
        loans_amount = 0.0
        if self.installments_ids:
            for installment in self.installments_ids:
                if not installment.paid:
                    loans_amount += installment.paid_amount
        self.loans_amount = loans_amount

    @api.depends('employee_id','termination_date')
    def compute_running_deductions(self):
        deductions_amount = 0.0
        unpaid_deductions = self.env['hr.deduction'].search(
            [('employee_id','=',self.employee_id.id),
            ('start_date','<=',self.termination_date),
            ('end_date','>=',self.termination_date),
            ('in_term_payslip','=',True),
            ('state','not in',('draft','cancel','refuse'))])
        for deduction in unpaid_deductions:
            left_months = relativedelta.relativedelta(deduction.end_date, self.termination_date)
            deductions_amount += deduction.de_amount * (left_months.months + 1)
        self.deductions_amount = deductions_amount
        if self.state == 'cancel':
            self.deductions_amount = 0.0

    # @api.depends('employee_id','termination_date')
    # def compute_running_incentives(self):
    #     incentives_amount = 0.0
    #     unpaid_incentives = self.env['hr.incentive.line'].search(
    #         [('employee_id', '=', self.employee_id.id),
    #         ('incentive_id.state', '=', 'approved'),
    #         ('incentive_id.date', '<=', self.termination_date),
    #         ('incentive_id.end_date', '>=', self.termination_date),
    #         ('incentive_id.in_term_payslip', '=', True)
    #         ])
    #     for incentive in unpaid_incentives:
    #         left_months = relativedelta.relativedelta(incentive.incentive_id.end_date, self.termination_date)
    #         incentives_amount += incentive.amount * (left_months.months + 1)
    #     self.incentives_amount = incentives_amount
    #     if self.state == 'cancel':
    #         self.incentives_amount = 0.0

    # @api.multi
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
            batch_id = self.env['hr.payslip.run'].create({
                'name' : ('Service Termination Batch of %s ') % (rec.employee_id.name),
                'state' : 'verify',
                'termination_id' : self.id
                })
            date = self.termination_date
            start_date = datetime(date.year, date.month, 1)
            payslip_vals = {
                'name': _('Service Termination Slip of %s ') % (rec.employee_id.name),
                'employee_id': rec.employee_id.id,
                'contract_id': rec.employee_id.contract_id.id,
                'struct_id': termination_struct_id.id,
                'type': 'service_termination',
                'termination_id': self.id,
                'payslip_run_id' : batch_id.id,
                'date_from' : start_date,
                'date_to' : self.last_joining_date}
            payslip = self.env['hr.payslip'].create(payslip_vals)
            payslip.sudo().compute_sheet()
            rec.write({'state': 'waiting_calculation'})
    
    def action_draft(self):
        payslip_ids = self.env['hr.payslip'].search([('termination_id','=',self.id)])
        batch_ids = payslip_ids.mapped('payslip_run_id')
        if payslip_ids:
            payslip_ids.action_payslip_cancel()
            if batch_ids:
                batch_ids.action_draft()
                batch_ids.unlink()
        self.employee_id.write({'active' : True})
        if self.employee_id.user_id:
            self.employee_id.user_id.write({'active' : True})
        self.write({'state':'draft'})    


    def get_batch(self):
        """
        A method read specific record from batcg.
        """
        self.ensure_one()
        action = self.env.ref('hr_payroll.action_hr_payslip_run_tree')
        result = action.read()[0]
        batch_ids = self.env['hr.payslip.run'].search([('termination_id','=',self.id)])
        result['domain'] = [('id', '=', batch_ids.ids)]
        return result

    def action_compute_details(self):
        for rec in self:
            rec.compute_running_loans()
            rec.compute_running_deductions()
            # rec.compute_running_incentives()
            unpaid_installments = self.env['hr.loan.line'].search(
                [('employee_id','=',self.employee_id.id),
                ('paid','=',False)])

            for installment in unpaid_installments:
                if installment.loan_id.state not in ('draft','cancel','refuse'):
                    installment.write({'termination_id':self.id})


    def action_submit(self):
        """
        A method to submit service termination and create clearance lines
        """
        for rec in self:
            rec.action_compute_details()
            rec.write({'state': 'submit'}) 

    @api.depends('last_joining_date','termination_date')
    def _compute_working_days(self):
        for rec in self:
            working_days = 0.0
            if rec.termination_date and rec.last_joining_date:
                d1 = datetime.strptime(str(rec.termination_date), '%Y-%m-%d')
                d2 = datetime.strptime(str(rec.last_joining_date), '%Y-%m-%d')
                working_days = (d2 - d1).days
            rec.working_days = working_days


    def action_done(self):
        """
        A method to set service termination done.
        """
        for rec in self:
            rec.write({'state': 'done'})
            rec.employee_id.contract_id.write(
                {'date_end': rec.termination_date + timedelta(days=rec.working_days), 'state': 'terminated'})
            rec.employee_id.job_id.write({'employee_ids': [(3, rec.employee_id.id)]})
            rec.employee_id.user_id.write({'active' : False})
            rec.employee_id.write({'active' : False})
        self.notification_method()


    def notification_method(self):
        if not self.employee_id.parent_id:
            raise ValidationError(_('this employee has no manager,please add for it'))
        if not self.employee_id.parent_id.address_home_id:
            raise ValidationError(_('this employee manager has no partner,please add for it'))
        else:
            message_id = self.env['mail.message'].create({
                'message_type': 'notification',
                'body': 'The Employee (%s) has complete the process of service termination.' % (self.employee_id.name),
                'subject': 'نهاية الخدمة',
                'model': self._name,
                'res_id': self.id,
                'partner_ids': [self.employee_id.parent_id.address_home_id.id],
                'author_id': self.env.user.partner_id.id,
                'record_name':'نهاية الخدمة للموظف (%s)' % (self.employee_id.name),
            })
            self.env['mail.notification'].create({
                'mail_message_id': message_id.id,
                'res_partner_id': self.employee_id.parent_id.address_home_id.id,
                'notification_type': 'inbox',
            })
            print('+++++++++++++++ message send success ####################')


class FinancialData(models.Model):
    _name = 'financial.data'

    fina_termina = fields.Many2one('hr.service.termination',string="financial Data")
    employee_id = fields.Many2one('hr.employee',string="Employee")
    department_id = fields.Many2one('hr.department')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('wait_payment', 'Waiting Payment'),
        ('paid', 'Paid'),
        ('close', 'Closed'),
        ('refuse', 'refused'),
    ], string='State', readonly=True, default='draft', track_visibility='onchange')

    is_clerance = fields.Boolean(string="is_clearance")


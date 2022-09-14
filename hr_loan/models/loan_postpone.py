# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

class HrLoanPostpone(models.Model):
	_name = 'hr.loan.postpone'
	_inherit = ['mail.thread']
	_rec_name = 'name'

	name = fields.Char('Reference',default=lambda self: _('New'), readonly=True)
	employee_id = fields.Many2one('hr.employee', string="Employee", store=True)
	emp_id = fields.Char(related="employee_id.emp_id" ,string="Employee ID")
	department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
									string="Department", store=True)
	
	loan_id = fields.Many2one('hr.loan', string="Loans",
							  domain="[('employee_id', '=', employee_id),('state','=','approve')]")
	loan_line_ids = fields.Many2many('hr.loan.line', string='Installments',
									 domain="[('loan_id', '=', loan_id),('paid','=',False)]")
	amount = fields.Float('Postpone Amount', compute="_get_total_to_paid")
	state = fields.Selection([
		('draft', 'Draft'),
		('submit', 'Submit'),
		('wait_dept_approve', 'Waiting Department Manager Approval'),
		('wait_hr_approve', 'Waiting HR Approval'),
		('wait_gm_approve', 'Waiting GM Approval'),
		('approve', 'Approved'),
		('cancel', 'Cancel'),
	], string="State", default='draft', tracking=5, copy=False, )
	date = fields.Date(string="Date", default=datetime.today())
	company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
	reason = fields.Text(string="Reason",required=True)
	residual_amount = fields.Float('Residual Amount', compute="_get_balance_amount")
	loan_amount = fields.Float(string="Loan Amount", compute="_get_balance_amount")
	is_type = fields.Selection(selection=[
		('postpone','Postpone'),
		('stop','Stop')
		],default='postpone')
	stop_months = fields.Integer()
	due_date = fields.Date(string='New Date of Payment',compute="_get_due_date",store=True)
	attachment_ids = fields.Many2many('ir.attachment', string="Loan Attachments",required=True)

	@api.depends('stop_months')
	def _get_due_date(self):
		self.due_date = False
		if self.is_type == 'stop':
			installment = min(self.env['hr.loan.line'].search([('loan_id','=',self.loan_id.id),('paid','!=',True),('loan_id.state','=','approve')]).ids)
			if installment:
				first_unpaid_installment = self.env['hr.loan.line'].browse(installment)            
				if self.stop_months:
					self.due_date = datetime.strptime(str(first_unpaid_installment.paid_date), '%Y-%m-%d') + relativedelta(months=self.stop_months)

	@api.depends('loan_id')
	def _get_balance_amount(self):
		for loan in self:
			loan.loan_amount = 0.0
			loan.residual_amount = 0.0
			if loan.loan_id:
				loan.loan_amount = loan.loan_id.loan_amount
				loan.residual_amount = loan.loan_id.balance_amount


	def _get_total_to_paid(self):
		"""
		A method to get total paid loan amount
		"""
		for loan in self:
			total_to_paid_amount = 0.00
			for line in loan.loan_line_ids:

				total_to_paid_amount += line.paid_amount
			loan.amount = total_to_paid_amount

	@api.model
	def create(self, vals):
		rec = super(HrLoanPostpone, self).create(vals)
		if not rec.loan_line_ids:
			if rec.is_type != 'stop':
				raise ValidationError(_('Please add Lines To Postpone.'))
		loan = rec.loan_id.name
		if vals['is_type'] == 'postpone':
			rec.name = loan + self.env['ir.sequence'].get('loan.postpone') or ' '
		if vals['is_type'] == 'stop':
			rec.name = loan + self.env['ir.sequence'].get('loan.stop') or ' '
		return rec

	def action_confirm(self):
		if self.is_type == 'postpone':
			if not self.attachment_ids:
				raise ValidationError(_('Please add Loan Attachment.'))
		self.write({'state': 'submit'})

	def action_submit(self):
		"""
		A method to Submit loan postpone
		"""
		self.write({'state': 'wait_dept_approve'})

	def action_dept_approve(self):
		self.write({'state': 'wait_hr_approve'})

	def action_hr_approve(self):
		self.write({'state': 'wait_gm_approve'})

	def action_approve(self):
		if self.is_type == 'stop':
			for line in self.loan_id.loan_line_ids:
				if not line.paid:
					line.write({'paid_date': datetime.strptime(str(line.paid_date), '%Y-%m-%d') + relativedelta(months=self.stop_months)})
			self.loan_id.write({'state': 'stop' })
		self.write({'state': 'approve'})

	def action_cancel(self):
		"""
		A method to confirm loan postpone
		"""
		self.write({'state': 'cancel' })

	def action_set_to_draft(self):
		"""
		A method to return loan postpone to draft
		"""
		self.write({'state': 'draft'})

	def _pause_loan(self):
		print('+++++++++++++ in _pause_loan')
		now = fields.Date.today()
		stoped_loans = self.env['hr.loan.postpone'].search([
			('is_type','=','stop'),
			('state','=','approve'),
			('loan_id.state','=','stop')])
		print('+++++++++++ stoped_loans',stoped_loans)
		if stoped_loans:
			for loan in stoped_loans:
				if loan.due_date == now:
					print('++++++ in iffffff')
					loan.loan_id.write({'state': 'approve' })


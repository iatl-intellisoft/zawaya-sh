# -*- coding: utf-8 -*-

from dateutil import relativedelta
from odoo import models,fields



class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	termination_id = fields.Many2one('hr.service.termination',string="Termination Record")

	def action_validate(self):
		res = super(HrPayslipRun, self).action_validate()
		if self.termination_id:
			self.termination_id.action_done()
			self.termination_id.employee_id.write({'active' : False})
			if self.termination_id.employee_id.user_id:
				self.termination_id.employee_id.user_id.write({'active' : False})
		return res

class HrPayslip(models.Model):
	""""""
	_inherit = 'hr.payslip'


	def compute_total_deduction(self):
		"""
		A method to compute total deduction amount
		"""
		total = 0.00
		for line in self.deduct_ids:
			month_no = 1
			if self.termination_id:
				month_no = relativedelta.relativedelta(line.end_date, self.termination_id.termination_date).months + 1
			total += line.de_amount * month_no
		self.total_deduct_amount = total

	def compute_total_incentive(self):
		"""
		A method to compute total incentive amount
		"""
		total = 0.00
		for line in self.incentive_ids:
			month_no = 1
			if self.termination_id:
				month_no = relativedelta.relativedelta(line.incentive_id.end_date, self.termination_id.termination_date).months + 1
			total += line.amount * month_no
		self.total_incentive_amount = total

	def get_loan(self):
		"""
		A method to get posted and approved employee's loan
		"""
		
		for rec in self:
			array = []
			rec.loan_ids.write({'payslip_id': False})
			if rec.termination_id:
				loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', rec.employee_id.id),
															('paid', '=', False),
															('loan_id.move_id.state', '=', 'posted'),
															('loan_id.state','=','approve')
															])
			else:
				loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', rec.employee_id.id),
															('paid', '=', False), ('paid_date', '>=', rec.date_from),
															('paid_date', '<=', rec.date_to),
															('loan_id.move_id.state', '=', 'posted'),
															('loan_id.state','=','approve')
															])

			loan_ids.write({'payslip_id': rec.id})
		return True


	def get_deduction(self):
		"""
		A method to get deduction
		"""
		for rec in self:
			if rec.termination_id:
				rec.deduct_ids = self.env['hr.deduction'].search([('employee_id', '=', rec.employee_id.id),
															  ('state', '=', 'approve'),
															  ('start_date', '<=', rec.date_to),
															  ('end_date', '>=', rec.date_to),
															  ('in_term_payslip', '=', True)
															  ]).ids
			else:
				rec.deduct_ids = self.env['hr.deduction'].search([('employee_id', '=', rec.employee_id.id),
															  ('state', '=', 'approve'),
															  '|',
															  '|',
															  '&',
															  ('start_date', '<=', rec.date_from),
															  ('end_date', '>',rec.date_from),
															 
															  '&',
															  ('start_date', '>=',rec.date_from),
															  ('end_date', '<=', rec.date_to),
															  
															  '&',
															  ('start_date','>=',rec.date_from),
															  ('end_date', '>=', rec.date_to),
															  ]).ids


	def get_incentive(self):
		"""
		A method to get incentive records
		"""
		for rec in self:
			if rec.termination_id:
				rec.incentive_ids = self.env['hr.incentive.line'].search([('employee_id', '=', rec.employee_id.id),
																		('incentive_id.incentive_type_id.payroll', '=',
																		True), ('incentive_id.state', '=', 'approved'),
																		('incentive_id.date', '<=', rec.date_to),
																		('incentive_id.end_date', '>=', rec.date_to),
																		('incentive_id.in_term_payslip', '=', True)
																		]).ids
			else:
				rec.incentive_ids = self.env['hr.incentive.line'].search([('employee_id', '=', rec.employee_id.id),
																		('incentive_id.incentive_type_id.payroll', '=',
																		True), ('incentive_id.state', '=', 'approved'),
																		('incentive_id.date', '<=', rec.date_to),
																		('incentive_id.end_date', '>=', rec.date_to)
																		]).ids

	def compute_sheet(self):
		"""
		A compute_sheet inherited to compute overtime in payslip.
		"""
		self.get_loan()
		self.get_incentive()
		self.get_deduction()
		return super(HrPayslip, self.sudo()).compute_sheet()


	def action_payslip_done(self):
		#inherit to change payslip to done and service termination to done
		res = super(HrPayslip, self.sudo()).action_payslip_done()
		for rec in self:
			if rec.termination_id:
				rec.termination_id.write({'state' : 'waiting_calculation'})
		return res



# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, _
from odoo.exceptions import UserError,ValidationError


class HrLoan(models.Model):
	_inherit = 'hr.loan'

	deduct_loans = fields.Selection([('week','Weekly'),('month','Monthly')],default='week')



	def compute_loan_line(self):
		"""
		A method to compute loan amount ber record using number of month.
		"""
		if self.loan_amount > (self.emp_salary * 2):
			print("___________________________",self.loan_amount,self.emp_salary)
			raise ValidationError(_('The Loan amount cannot exceed twice the salary.'))
		dates = []
		diff = 0.0
		total = 0.0
		loan_line = self.env['hr.loan.line']
		loan_line.search([('loan_id', '=', self.id)]).unlink()
		amount_per_time = 0
		for loan in self:

			date_start_str = datetime.strptime(str(loan.payment_start_date), '%Y-%m-%d')

			counter = 1

			if loan.deduct_loans == 'month':

				amount_per_time = int(loan.loan_amount / loan.no_month)

				for i in range(1, loan.no_month + 1):
					line_id = loan_line.create({
						'paid_date': date_start_str,
						'paid_amount': amount_per_time,
						'payment_date': date_start_str,
						'employee_id': loan.employee_id.id,
						'loan_id': loan.id})
					counter += 1
					date_start_str = date_start_str + relativedelta(months=1)

			if loan.deduct_loans == 'week':
				amount_per_time = int(loan.loan_amount / 7)

				for i in range(1, 7 + 1):
					line_id = loan_line.create({
						'paid_date': date_start_str,
						'paid_amount': amount_per_time,
						'payment_date': date_start_str,
						'employee_id': loan.employee_id.id,
						'loan_id': loan.id})
					counter += 1
					date_start_str = date_start_str + relativedelta(weeks=1)

			for line in loan.loan_line_ids:
				total = total + line.paid_amount
				diff = loan.total_amount - total
				if isinstance(line.paid_date, date):
					dates.append(line.paid_date)
			date_m = max(dates)
			if date_m:
				line.write({'paid_amount': amount_per_time + diff})
		return True
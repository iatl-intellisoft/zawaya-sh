

from odoo import api, fields, models,_

class Employees(models.Model):
	_inherit = 'hr.employee'

	annual_remaining_days = fields.Integer(string="Annual Remaining Days",compute="_calc_remaining_days")

	@api.depends('remaining_leaves')
	def _calc_remaining_days(self):
		for rec in self:
			alloaction = self.env['hr.leave.allocation'].search([('employee_id','=',rec.id),
				('holiday_status_id.can_be_sold','=',True)])
			if alloaction:
				for alloc in alloaction:
					rec.annual_remaining_days += alloc.number_of_days_display - alloc.leaves_taken
			else:
				rec.annual_remaining_days = 0.0
	

class HrIncentive(models.Model):
	_inherit = 'hr.incentive'

	leave_id = fields.Many2one('hr.leave')

class HrLoan(models.Model):
	_inherit = 'hr.loan'

	leave_id = fields.Many2one('hr.leave')
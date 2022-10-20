

from odoo import api, fields, models, tools, SUPERUSER_ID


class LeaveTypes(models.Model):
	_inherit = 'hr.leave.type'

	is_annual = fields.Boolean(default=False,string="Is Annual Time Off ")
	is_sick = fields.Boolean(default=False,string="Is Sick Time Off ")
	is_work_injury = fields.Boolean(default=False,string="Is Work Injury")
	need_clearance = fields.Boolean(default=False,string="Clearance Is Required")
	can_be_sold = fields.Boolean(string="Can Be Sold") 


class Allocation(models.Model):
	_inherit = 'hr.leave.allocation'

	@api.depends('employee_id', 'holiday_status_id', 'taken_leave_ids.number_of_days', 'taken_leave_ids.state')
	def _compute_leaves(self):
		for allocation in self:
			allocation.max_leaves = allocation.number_of_hours_display if allocation.type_request_unit == 'hour' else allocation.number_of_days
			allocation.leaves_taken = sum(taken_leave.number_of_hours_display if taken_leave.leave_type_request_unit == 'hour' else taken_leave.number_of_days\
				for taken_leave in allocation.taken_leave_ids\
				if taken_leave.state == 'validate')

			if allocation.employee_id:
				sell_times = self.env['sell.time.off'].search([('employee_id','=',allocation.employee_id.id),
					('request_date','>=',allocation.date_from),('request_date','<=',allocation.date_to),('state','=','approve')])
				days = 0
				if sell_times:
					for time in sell_times:
						days += time.days_to_sell
				allocation.leaves_taken = allocation.leaves_taken + days

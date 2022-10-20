
from odoo import api, fields, models, tools, SUPERUSER_ID,_
from odoo.exceptions import AccessError, UserError, ValidationError

class LeaveClearanceLine(models.Model):
	_name = 'leave.clearance.line'

	department_id = fields.Many2one('hr.department', string='Department', required=True)
	cleared = fields.Boolean('Cleared', readonly=True)
	notes = fields.Text('Notes')
	approve_by = fields.Many2one('hr.employee', string='Approve By')
	leave_id = fields.Many2one('hr.leave')

	def set_approve(self):
		"""
		A method to approve service termination clearance records.
		"""
		# current employee
		employee_obj = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

		# if self.department_id.manager_id.id != employee_obj.id:
		# 	raise UserError(_("Only %s manager can approve this clearance") % (self.department_id.name))

		self.approve_by = employee_obj.id
		self.cleared = True

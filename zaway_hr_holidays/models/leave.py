
import logging
from collections import namedtuple, defaultdict
from datetime import datetime, timedelta, time
from pytz import timezone, UTC
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression
from odoo.tools.translate import html_translate

_logger = logging.getLogger(__name__)

class Leave(models.Model):
	_inherit = 'hr.leave'

	sequence = fields.Char(string='Code', readonly=True)
	state = fields.Selection([
		('draft', 'To Submit'),
		('confirm', 'To Approve'),
		('wait_dept_approve', 'Waiting Department Manager Approval'),
		('wait_hr_approve', 'Waiting HR Approval'),
		('wait_gm_approve', 'Waiting GM Approval'),
		('validate1', 'Second Approval'),
		('validate', 'Approved'),
		('refuse', 'Refused'),
		('stop', 'Stoped'),
		], string='Status', compute='_compute_state', store=True, tracking=True, copy=False, readonly=False,
		help="The status is set to 'To Submit', when a time off request is created." +
		"\nThe status is 'To Approve', when time off request is confirmed by user." +
		"\nThe status is 'Refused', when time off request is refused by manager." +
		"\nThe status is 'Approved', when time off request is approved by manager.")
	job_id = fields.Many2one('hr.job', string="Job Position",compute='_compute_employee_data',readonly=False)
	department_id = fields.Many2one(
		'hr.department', compute='_compute_department_id', string='Department', readonly=False)
	address = fields.Char(compute='_compute_employee_data', readonly=False)
	contract_start_date = fields.Date('Contract Start Date', compute="_compute_employee_data", tracking=True,
		help="Start date of the contract.")
	time_off_location = fields.Char()
	time_off_address = fields.Char()
	back_date = fields.Date()
	phone = fields.Char()
	alternative_employee_id = fields.Many2one('hr.employee')
	relative_name = fields.Char('Name of nearest relative ')
	relative_phone = fields.Char('Phone of nearest relative ')
	need_allowance = fields.Boolean(default=False)
	incentive_ids = fields.One2many('hr.incentive','leave_id')
	need_advance_salary = fields.Boolean(default=False)
	advance_salary = fields.Float()
	leave_expences = fields.Float('Time Off Expenses')
	loan_ids = fields.One2many('hr.loan','leave_id')
	stop = fields.Boolean(default=False)
	stop_date = fields.Date(readonly=True)
	stop_reason = fields.Text(readonly=True)
	old_end_date = fields.Date('Time Off Old End Date')
	old_number_of_days = fields.Float('Time Off Old Duration')
	is_annual = fields.Boolean(default=False,string="Is Annual Time Off ",related="holiday_status_id.is_annual")
	is_sick = fields.Boolean(default=False,string="Is Sick Time Off ",related="holiday_status_id.is_sick")
	is_work_injury = fields.Boolean(default=False,string="Is Work Injury",related="holiday_status_id.is_work_injury")
	disease_type = fields.Char()
	need_clearance = fields.Boolean(default=False,string="Clearance Is Required",related="holiday_status_id.need_clearance")
	leave_clearance_ids = fields.One2many('leave.clearance.line', 'leave_id',string='Clearance Department', )
	company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
	leave_certificate_website_description = fields.Html('Body Template', sanitize_attributes=False,
												   translate=html_translate,compute="get_leave_certificate_website_description")
	leave_certificate_template_id = fields.Many2one('mail.template', string='Time Off Certificate Template',
											   related='company_id.leave_certificate_template_id')
	date_request = fields.Date(default=fields.Date.today())
	sick_website_description = fields.Html('Body Template', sanitize_attributes=False,
												   translate=html_translate,compute="get_sick_website_description")
	sick_template_id = fields.Many2one('mail.template', string='Sick Time Off Template',
											   related='company_id.sick_template_id')
	move_id = fields.Many2one('account.move', string='Move',copy=False,readonly=True)
	
	@api.onchange('need_advance_salary')
	def check_need_advance_salary(self):
		if self.employee_id and self.need_advance_salary:
			self.advance_salary = self.employee_id.contract_id.wage

	def first_confirm(self):
		if self.holiday_status_id.support_document:
			if not self.supported_attachment_ids:
				raise UserError(_('This time off required supported document, Please attach it .'))

		if self.need_clearance:
			for clearance in self.leave_clearance_ids:
				if not clearance.cleared:
					raise UserError(_('You must complete your clearance firstly.'))

		self.write({'state': 'wait_dept_approve'})

	def dept_confirm(self):
		self.write({'state': 'wait_hr_approve'})

	def hr_confirm(self):
		self.write({'state': 'wait_gm_approve'})

	@api.model
	def create(self, vals):
		record = super(Leave, self).create(vals)
		record.sequence =  self.env['ir.sequence'].get('hr.leave') or ' '

		company = self.env['res.company'].search([('id', '=', self.env.company.id)])
		leave = self.search([('id', '=', record.id)])
		for department in company.leave_clearance_ids:
			leave.write({'leave_clearance_ids': [
			(0, 0, {'leave_id': record.id, 'department_id': department.id})]})
			# create mail activity for eacth department manager
			if not department.manager_id.id:
				raise UserError(_("Please Add Manager To %s Department") % (department.name))
			if not department.manager_id.user_id.id:
				raise UserError(_("Please Add User To %s ") % (department.manager_id.name))
			activity = self.env['mail.activity'].create({
				'note': "Please Approve " + str(record.employee_id.name) + " Clearance",
				'summary': 'Employee Clearance Approval',
				'res_id': record.id,
				'user_id': department.manager_id.user_id.id,
				'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
				'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.leave')], limit=1).id,
			})
		return record

	@api.depends('leave_certificate_template_id', 'leave_certificate_template_id.body_html')
	def get_leave_certificate_website_description(self):
		"""
		A method to create leave certificate website description template
		"""
		for rec in self:
			rec.leave_certificate_website_description = ''
			# rec.leave_certificate_website_description += rec.leave_certificate_website_description
			if rec.leave_certificate_template_id and rec.id:
				fields = ['body_html']
				template_values = rec.leave_certificate_template_id.generate_email([rec.id], fields=fields)
				rec.leave_certificate_website_description = template_values[rec.id].get('body_html')

	@api.depends('sick_template_id', 'sick_template_id.body_html')
	def get_sick_website_description(self):
		"""
		A method to create sick leave website description template
		"""
		for rec in self:
			# rec.sick_website_description += rec.sick_website_description
			rec.sick_website_description = ''
			if rec.sick_template_id and rec.id:
				fields = ['body_html']
				template_values = rec.sick_template_id.generate_email([rec.id], fields=fields)
				rec.sick_website_description = template_values[rec.id].get('body_html')

	@api.depends('employee_id', 'holiday_type')
	def _compute_employee_data(self):
		for holiday in self:
			if holiday.employee_id:
				holiday.job_id = holiday.employee_id.job_id
				holiday.address = holiday.employee_id.home_address
				holiday.contract_start_date = holiday.employee_id.contract_id.date_start
			else:
				holiday.job_id = False
				holiday.address = False
				holiday.contract_start_date = False

	@api.onchange('employee_id')
	def _domain_alternative_employee(self):
		if self.employee_id:
			return {'domain': {'alternative_employee_id': [('id', '!=', self.employee_id.id)]}}

	def open_incentive(self):
		view_id = self.env.ref('hr_incentive.view_hr_incentive_form').id
		return {
			'name': 'Create Incentive',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'target': 'new',
			'res_model': 'hr.incentive',
			'view_id': view_id,
			'context': {'default_leave_id':self.id ,'default_types':'employee' ,'default_employee_id':self.employee_id.id}
		}

	def open_loans(self):
		view_id = self.env.ref('hr_loan.view_hr_loan_form').id
		return {
			'name': 'Create Loan',
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'target': 'new',
			'res_model': 'hr.loan',
			'view_id': view_id,
			'context': {'default_leave_id':self.id ,'default_employee_id':self.employee_id.id,'default_reason':'For Time Off' }
		}

	def action_approve(self):
		# if validation_type == 'both': this method is the first approval approval
		# if validation_type != 'both': this method calls action_validate() below
		if any(holiday.state != 'wait_gm_approve' for holiday in self):
			raise UserError(_('Time off request must be confirmed ("GM Approve") in order to approve it.'))

		current_employee = self.env.user.employee_id
		self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})

		# Post a second message, more verbose than the tracking message
		for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
			holiday.message_post(
				body=_(
					'Your %(leave_type)s planned on %(date)s has been accepted',
					leave_type=holiday.holiday_status_id.display_name,
					date=holiday.date_from
				),
				partner_ids=holiday.employee_id.user_id.partner_id.ids)

		self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
		if not self.env.context.get('leave_fast_create'):
			self.activity_update()

		return True

	def action_validate(self):
		current_employee = self.env.user.employee_id
		leaves = self._get_leaves_on_public_holiday()
		if leaves:
			raise ValidationError(_('The following employees are not supposed to work during that period:\n %s') % ','.join(leaves.mapped('employee_id.name')))

		if any(holiday.state not in ['confirm', 'validate1','wait_gm_approve'] and holiday.validation_type != 'no_validation' for holiday in self):
			raise UserError(_('Time off request must be confirmed in order to approve it.'))

		self.write({'state': 'validate'})

		leaves_second_approver = self.env['hr.leave']
		leaves_first_approver = self.env['hr.leave']

		for leave in self:
			if leave.validation_type == 'both':
				leaves_second_approver += leave
			else:
				leaves_first_approver += leave

			if leave.holiday_type != 'employee' or\
				(leave.holiday_type == 'employee' and len(leave.employee_ids) > 1):
				if leave.holiday_type == 'employee':
					employees = leave.employee_ids
				elif leave.holiday_type == 'category':
					employees = leave.category_id.employee_ids
				elif leave.holiday_type == 'company':
					employees = self.env['hr.employee'].search([('company_id', '=', leave.mode_company_id.id)])
				else:
					employees = leave.department_id.member_ids

				conflicting_leaves = self.env['hr.leave'].with_context(
					tracking_disable=True,
					mail_activity_automation_skip=True,
					leave_fast_create=True
				).search([
					('date_from', '<=', leave.date_to),
					('date_to', '>', leave.date_from),
					('state', 'not in', ['cancel', 'refuse']),
					('holiday_type', '=', 'employee'),
					('employee_id', 'in', employees.ids)])

				if conflicting_leaves:
					# YTI: More complex use cases could be managed in master
					if leave.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
						raise ValidationError(_('You can not have 2 time off that overlaps on the same day.'))

					# keep track of conflicting leaves states before refusal
					target_states = {l.id: l.state for l in conflicting_leaves}
					conflicting_leaves.action_refuse()
					split_leaves_vals = []
					for conflicting_leave in conflicting_leaves:
						if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
							continue

						# Leaves in days
						if conflicting_leave.date_from < leave.date_from:
							before_leave_vals = conflicting_leave.copy_data({
								'date_from': conflicting_leave.date_from.date(),
								'date_to': leave.date_from.date() + timedelta(days=-1),
								'state': target_states[conflicting_leave.id],
							})[0]
							before_leave = self.env['hr.leave'].new(before_leave_vals)
							before_leave._compute_date_from_to()

							# Could happen for part-time contract, that time off is not necessary
							# anymore.
							# Imagine you work on monday-wednesday-friday only.
							# You take a time off on friday.
							# We create a company time off on friday.
							# By looking at the last attendance before the company time off
							# start date to compute the date_to, you would have a date_from > date_to.
							# Just don't create the leave at that time. That's the reason why we use
							# new instead of create. As the leave is not actually created yet, the sql
							# constraint didn't check date_from < date_to yet.
							if before_leave.date_from < before_leave.date_to:
								split_leaves_vals.append(before_leave._convert_to_write(before_leave._cache))
						if conflicting_leave.date_to > leave.date_to:
							after_leave_vals = conflicting_leave.copy_data({
								'date_from': leave.date_to.date() + timedelta(days=1),
								'date_to': conflicting_leave.date_to.date(),
								'state': target_states[conflicting_leave.id],
							})[0]
							after_leave = self.env['hr.leave'].new(after_leave_vals)
							after_leave._compute_date_from_to()
							# Could happen for part-time contract, that time off is not necessary
							# anymore.
							if after_leave.date_from < after_leave.date_to:
								split_leaves_vals.append(after_leave._convert_to_write(after_leave._cache))

					split_leaves = self.env['hr.leave'].with_context(
						tracking_disable=True,
						mail_activity_automation_skip=True,
						leave_fast_create=True,
						leave_skip_state_check=True
					).create(split_leaves_vals)

					split_leaves.filtered(lambda l: l.state in 'validate')._validate_leave_request()

				values = leave._prepare_employees_holiday_values(employees)
				leaves = self.env['hr.leave'].with_context(
					tracking_disable=True,
					mail_activity_automation_skip=True,
					leave_fast_create=True,
					no_calendar_sync=True,
					leave_skip_state_check=True,
				).create(values)

				leaves._validate_leave_request()

		leaves_second_approver.write({'second_approver_id': current_employee.id})
		leaves_first_approver.write({'first_approver_id': current_employee.id})

		employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
		employee_requests._validate_leave_request()
		if not self.env.context.get('leave_fast_create'):
			employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
		
		if self.need_advance_salary or self.leave_expences > 0.0:
			self.create_bill()
		return True

	def create_bill(self):
		if not self.env.company.salary_expences_account_id:
			raise ValidationError(_('Please Enter Time Off Salary/Expenses Account In Setting'))
		if not self.employee_id.address_home_id:
			raise ValidationError(_('Please Enter Partner For This Employee'))
		amount = 0.0
		if self.need_advance_salary:
			amount += self.advance_salary
		if self.leave_expences:
			amount += self.leave_expences
		move = self.env['account.move'].create({
			'move_type': 'in_receipt',
			'partner_id': self.employee_id.address_home_id.id,
			'invoice_line_ids': [
				(0, None, {
					'quantity': 1,
					'price_unit': amount,
					'name': self.sequence,
					'account_id': self.env.company.salary_expences_account_id.id,
				}),
			]})
		self.move_id = move


class HrEmployeeBase(models.AbstractModel):
	_inherit = "hr.employee.base"

	current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Time Off Status",
		selection=[
			('draft', 'To Submit'),
			('confirm', 'To Approve'),
			('wait_dept_approve', 'Waiting Department Manager Approval'),
			('wait_hr_approve', 'Waiting HR Approval'),
			('wait_gm_approve', 'Waiting GM Approval'),
			('validate1', 'Second Approval'),
			('validate', 'Approved'),
			('refuse', 'Refused'),
			('stop', 'Stoped'),
		])
	
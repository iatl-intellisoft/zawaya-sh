
from odoo import models, fields, api, _

class HrLoanBatch(models.Model):
	_name = 'hr.loan.batch'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_rec_name = 'code'


	code = fields.Char(string='Code')
	request_date = fields.Date(string='Request Date', required=True,
							default=fields.Date.today())
	line_ids = fields.One2many('loan.batch.line','batch_id')
	amount = fields.Float('Loan Amount',required=True)
	loan_type = fields.Many2one('loan.type', string="Loan Type", index=True, required=True, ondelete='restrict')
	state = fields.Selection([
		('draft', 'Draft'),
		('submit', 'Submit'),
		('wait_dept_approve', 'Waiting Department Manager Approval'),
		('wait_hr_approve', 'Waiting HR Approval'),
		('wait_gm_approve', 'Waiting GM Approval'),
		('approve', 'Approved'),
		('cancel', 'Cancel'),
	], string="State", default='draft', tracking=5, copy=False, )
	note = fields.Text(required=True)
	activity_id = fields.Many2one('mail.activity', string='Activity')
	company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
	

	@api.onchange('loan_type')
	def get_loan_amount(self):
		for rec in self:
			rec.amount = 0.0
			if rec.loan_type:
				rec.amount = rec.loan_type.amount


	@api.model
	def create(self, vals):
		"""
		A create method was inherited to create loan.
		"""
		vals['code'] = self.env['ir.sequence'].get('hr.loan.batch') or '/'
		res = super(HrLoanBatch, self).create(vals)
		return res

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
		self.compute_gm_approve_notification()
		for line in self.line_ids:
			self.env['hr.loan.line'].create({
				'employee_id': line.employee_id.id,
				'paid_date':self.request_date,
				'loan_batch_id': self.id,
				'paid_amount':line.amount,
				})
		self.write({'state': 'approve'})

	@api.model
	def compute_gm_approve_notification(self):
		users = self.env['res.groups'].search([('id', '=',self.env.ref('hr_loan.group_hr_general_manager').id)],limit=1).users
		if users:
			for rec in self:
				for user in users:
					vals = {
						'activity_type_id': self.env['mail.activity.type'].sudo().search([('name', 'like', 'To Do')],limit=1).id,
						'res_id': rec.id,
						'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'hr.loan.batch')],
																		   limit=1).id,
						'user_id': user.id,
						'summary': rec.code + 'GM approve needed fo loan',
					}
				self.activity_id = self.env['mail.activity'].sudo().create(vals).id


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



class LoanBatchLine(models.Model):
	_name = 'loan.batch.line'

	employee_id = fields.Many2one('hr.employee')
	department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
									string="Department", store=True)
	job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
	emp_id = fields.Char(related="employee_id.emp_id", readonly=True, string="Job Position")
	contract_id = fields.Many2one('hr.contract',related="employee_id.contract_id",store=True)
	wage = fields.Monetary(related="contract_id.wage")
	amount = fields.Float(compute="get_amount")
	batch_id = fields.Many2one('hr.loan.batch')
	company_id = fields.Many2one('res.company',
		default=lambda self: self.env.company, required=True)
	currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)

	@api.depends('batch_id')
	def get_amount(self):
		for rec in self:
			rec.amount = 0.0
			if rec.batch_id:
				rec.amount = rec.batch_id.amount



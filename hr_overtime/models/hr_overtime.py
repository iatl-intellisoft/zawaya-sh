# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2018-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import datetime
import calendar
from odoo.tools.translate import html_translate

class overtime(models.Model):
	_inherit = 'hr.payroll.structure'

	working_day_rate = fields.Float(string="Working Days Rate", readonly=False)
	weekend_rate = fields.Float(string="Weekends Rate", readonly=False)
	public_holiday_rate = fields.Float(string="Public Holidays Rates", readonly=False)
	overtime_rule_id = fields.Many2one('hr.salary.rule', string='Rule Salary use when overtiome type by payroll')


class Employee(models.Model):
	""""""
	_inherit = 'hr.employee'

	allow_overtime = fields.Boolean('Allow Overtime', )


class HrOvertime(models.Model):
	""""""
	_name = 'hr.overtime'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	_rec_name = 'sequence'

	sequence = fields.Char(readonly='1')

	paid = fields.Boolean(string='Is Paid')

	payslip_id = fields.Many2one('hr.payslip', ondelete='set null', string='Payslip')

	employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
								  domain=[('allow_overtime', '=', 'True')])
	department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',store=True)
	start_date = fields.Date(string='Start Date', required=True)
	end_date = fields.Date(string='End Date', required=True)
	line_ids = fields.One2many('hr.overtime.line', 'overtime_id', string='Overtime Details',
							   copy=True)
	batch_id = fields.Many2one('hr.overtime.batch', required=False, invisible="true",
							   ondelete='cascade')
	company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states={'draft': [(
		'readonly', False)], 'submit': [('readonly', False)]}, default=lambda self: self.env.user.company_id.id)

	company_overtime_type = fields.Selection([('payroll', 'Through Payroll'), ('receipt', 'Through Receipt')],
											 related='company_id.overtime_type',store=True)
	working_day_rate = fields.Float(string="Working Days Rate")
	weekend_rate = fields.Float(string="Weekends Rate")
	public_holiday_rate = fields.Float(string="Public Holidays Rates")
	overtime_rule_id = fields.Many2one('hr.salary.rule', string='Rule Salary *', compute='_amount_all',store=True )

	state = fields.Selection([
		('draft', 'Draft'),
		('submit', 'Submit'),
		('wait_dept_approve', 'Waiting Department Manager Approval'),
		('wait_hr_approve', 'Waiting HR Approval'),
		('approve', 'Approved'),
		('cancel', 'Cancel'),
	], string="State", default='draft', tracking=5, copy=False, )

	total_working_hours = fields.Float('Total Working Hours', compute='_amount_all',store=True)
	total_weekend = fields.Float('Total Weekend Hours', compute='_amount_all',store=True)
	total_public_holiday = fields.Float('Total Holiday Hours', compute='_amount_all',store=True)
	total_amount = fields.Float('Total Amount', compute='_get_total_amount',store=True)
	total_hours = fields.Float('Total Hours', compute='_amount_all_config',store=True)
	hour_wage = fields.Float('Hour Wage', compute='_amount_all')

	journal_id = fields.Many2one('account.journal', domain=[('type', '=', 'purchase')],
								 invisible='company overtiem_type != payroll', requried=True)
	account_id = fields.Many2one('account.account', invisible='company overtime_type != payroll')
	move_id = fields.Many2one('account.move', invisible='empty', readonly=True)
	bank_id = fields.Many2one('res.bank', readonly=False, store=True)


	def remove_batch_id(self):
		"""
		A method to make batch equal null
		"""
		for rec in self:
			rec.batch_id = False

	@api.model
	def create(self, vals):
		"""
		A create method inherited to create overtime sequence.
		"""
		seq = self.env['ir.sequence'].next_by_code('overtime.sequence') or '/'
		vals['sequence'] = seq
		return super(HrOvertime, self).create(vals)

	@api.onchange('employee_id')
	def onch_emp_comp(self):
		self.working_day_rate = self.employee_id.contract_id.struct_id.working_day_rate or self.company_id.working_day_rate
		self.weekend_rate = self.employee_id.contract_id.struct_id.weekend_rate or self.company_id.weekend_rate
		self.public_holiday_rate = self.employee_id.contract_id.struct_id.public_holiday_rate or self.company_id.public_holiday_rate

	@api.depends('total_hours')
	def _get_total_amount(self):
		"""
		A method to compute total overtime amount per overtime record.
		"""
		for rec in self:
			rec.total_amount = 0.0
			rec.hour_wage = 0.0
			if rec.employee_id:
				if rec.employee_id.active:
					domain = [('employee_id', '=', rec.employee_id.id),
							  ('state', 'in', ['open', 'offer'])]
				else:
					domain = [('employee_id', '=', rec.employee_id.id)]
				contract = self.env['hr.contract'].search(domain,order = 'date_start desc' ,limit=1)
				if not contract and rec.employee_id.active == True:
					raise ValidationError(_("There is no running contract for this Employee %s.") % (rec.employee_id.name))

				# overtime_rule = contract.struct_id.overtime_rule_id or rec.company_id.overtime_rule_id
				# rec.total_amount = 0.0
				# if overtime_rule:
				# 	rec.total_amount = rec.total_hours * overtime_rule.compute_rule_amount(rec.employee_id)
				rec.total_amount = rec.total_hours * contract.wage_per_hour

	@api.depends('line_ids.hours','line_ids','employee_id','company_id','working_day_rate'\
		,'weekend_rate','public_holiday_rate')
	def _amount_all(self):
		"""
		Compute the total amounts of Overtime.
		"""
		for rec in self:
			total = 0.0
			total_work = 0.0
			total_weekend = 0.0
			total_holiday = 0.0
			hour_wage = 0.0

			overtime_rule = False
			overtime_type = rec.company_id and rec.company_id.overtime_type or 'receipt'
			if rec.employee_id:
				if rec.employee_id.active:
					domain = [('employee_id', '=', rec.employee_id.id),
							  ('state', 'in', ['open', 'offer'])]
				else:
					domain = [('employee_id', '=', rec.employee_id.id)]
				contract = self.env['hr.contract'].search(domain,order = 'date_start desc' ,limit=1)
				if not contract and rec.employee_id.active == True:
					raise ValidationError(_("There is no running contract for this Employee %s.") % (rec.employee_id.name))

				# if contract.struct_id.overtime_rule_id or rec.company_id.overtime_rule_id:
				# 	overtime_rule = contract.struct_id.overtime_rule_id or rec.company_id.overtime_rule_id
				for line in rec.line_ids:
					total += line.hours
					if line.overtime_type == 'working_day':
						total_work += line.hours
					if line.overtime_type == 'weekend':
						total_weekend += line.hours
					if line.overtime_type == 'public_holiday':
						total_holiday += line.hours

				# if overtime_rule:
				# 	hour_wage = overtime_rule.compute_rule_amount(rec.employee_id)
				hour_wage = contract.wage_per_hour
			rec.update({
				'total_working_hours': total_work,
				'total_weekend': total_weekend,
				'total_public_holiday': total_holiday,
				'hour_wage': hour_wage,
				'overtime_rule_id': overtime_rule,
				'company_overtime_type': overtime_type,
			})

	@api.constrains('end_date', 'start_date', 'line_ids')
	def _check_date(self):
		"""
		A method to check overtime date.
		"""
		for order in self:
			for line in order.line_ids:
				if line.date < order.start_date or line.date > order.end_date:
					raise ValidationError(_("The Date should be within overtime range !"))

	@api.depends('total_working_hours', 'total_weekend', 'total_public_holiday', 'company_id')
	def _amount_all_config(self):
		"""
		A method to compute total overtime hours amount.
		"""
		for rec in self:
			rec.total_hours = 0.0
			if rec.employee_id:
				if rec.employee_id.active:
					domain = [('employee_id', '=', rec.employee_id.id),
							  ('state', 'in', ['open', 'offer'])]
				else:
					domain = [('employee_id', '=', rec.employee_id.id)]
				contract = self.env['hr.contract'].search(domain,order = 'date_start desc' ,limit=1)
				if not contract and rec.employee_id.active == True:
					raise ValidationError(_("There is no running contract for this Employee %s.") % (rec.employee_id.name))

				working_day_rate = contract.struct_id.working_day_rate or rec.company_id.working_day_rate
				weekend_rate = contract.struct_id.weekend_rate or rec.company_id.weekend_rate
				public_holiday_rate = contract.struct_id.public_holiday_rate or rec.company_id.public_holiday_rate

				rec.total_hours = (working_day_rate * rec.total_working_hours) + (weekend_rate * rec.total_weekend) + (public_holiday_rate * rec.total_public_holiday)
				

	def action_draft(self):
		"""
		A method to set overtime draft.
		"""
		self.write({'state': 'draft'})

	def action_cancel(self):
		"""
		A method to cancel overtime.
		"""
		for rec in self:
			if rec.paid:
				raise ValidationError(_("You can not delet paid over time !"))
			elif not rec.paid:
				if rec.payslip_id:
					if rec.payslip_id.state == "cancel":
						rec.write({'state': 'cancel', 'payslip_id': False})
					else:
						raise ValidationError(_("In order to cancel this over time you must cancel the payslip First!"))
				else:
					rec.write({'state': 'cancel'})

	def action_confirm(self):
		self.write({'state': 'submit'})

	def action_dept_approve(self):
		self.write({'state': 'wait_hr_approve'})

	def action_approve(self):
		"""
		A method to approve overtime.
		"""
		if self.batch_id:
			raise UserError(_("You should approve this overtime from it's batch "))

		if self.company_id.overtime_type == 'receipt':
			for rec in self:
				if not rec.account_id:
					raise UserError(_("Please select an account"))

				if not rec.journal_id:
					raise UserError(_("please select journal "))    

				move_id = self.env['account.move'].sudo().create([
					{
						'date': rec.start_date,
						'partner_id': rec.employee_id.address_home_id.id,
						'journal_id': rec.journal_id.id,
						'move_type': 'in_receipt',
						'line_ids': [
							(0, 0, {
								'name': rec.sequence,
								'partner_id': rec.employee_id.address_home_id.id,
								'account_id': rec.account_id.id,
								'price_unit': rec.total_amount,
								'debit': rec.total_amount,
							}
							 ),
							(0, 0, {
								'name': rec.sequence,
								'partner_id': rec.employee_id.address_home_id.id,
								'account_id': rec.employee_id.address_home_id.property_account_payable_id.id,
								'price_unit': rec.total_amount,
								'credit': rec.total_amount,
								'account_internal_type': 'payable',
								'exclude_from_invoice_tab': True
							}
							 ), ], }])

				self.write({'state': 'approve', 'move_id': move_id.id})

		if self.company_id.overtime_type == 'payroll':
			self.write({'state': 'approve', })

	def action_submit(self):
		"""
		A method to submit overtime.
		"""
		if not self.employee_id:
			raise ValidationError(_("You must first select an employee."))
		if not self.line_ids:
			raise ValidationError(_("You must enter overtime details before submit it."))

		self.write({'state': 'wait_dept_approve'})

	def unlink(self):
		"""
		A method to delete overtime.
		"""
		for overtime in self:
			if overtime.state not in ('draft',):
				raise UserError(_('You can not delete record not in draft state.'))

			return super(HrOvertime, self).unlink()


class OvertimeLine(models.Model):
	""""""
	_name = "hr.overtime.line"

	date = fields.Date('Date', required='1')
	overtime_type = fields.Selection([
		('working_day', 'Working Day'),
		('weekend', 'Weekend'),
		('public_holiday', 'Holiday')], string='Overtime Type', required='1')
	hours = fields.Float('Hours', required='1')
	overtime_id = fields.Many2one('hr.overtime', required=True, invisible="true",
								  ondelete='cascade')
	state = fields.Selection([
		('draft', 'Draft'),
		('submit', 'Submit'),
		('waiting', 'waiting Approval'),
		('approve', 'Approved'),
		('cancel', 'Cancel'), ], 'Status', track_visibility='onchange', required=True,
		copy=False, default='draft', related='overtime_id.state')


class ResPartner(models.Model):
	""""""
	_inherit = 'hr.employee'

	overtime_count = fields.Integer(compute='_compute_overtime_count', string='Overtime Count')

	def _compute_overtime_count(self):
		""""""
		overtime_data = self.env['hr.overtime'].read_group(domain=[('employee_id', 'child_of', self.ids)],
														   fields=['employee_id'], groupby=['employee_id'])
		# read to keep the child/parent relation while aggregating the read_group result in the loop
		employee_child_ids = self.read(['child_ids'])
		mapped_data = dict([(m['employee_id'][0], m['employee_id_count']) for m in overtime_data])
		for partner in self:
			# let's obtain the partner id and all its child ids from the read up there
			item = next(p for p in employee_child_ids if p['id'] == partner.id)
			partner_ids = [partner.id] + item.get('child_ids')
			# then we can sum for all the partner's child
			partner.overtime_count = sum(mapped_data.get(child, 0) for child in partner_ids)


class OverTimeBatch(models.Model):
	""""""
	_name = 'hr.overtime.batch'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	sequence = fields.Char(readonly=True)
	name = fields.Char(string='Description', required=True)
	start_date = fields.Date(string='Start Date', required=True)
	end_date = fields.Date(string='End Date', required=True
						   )
	employee_overtime_ids = fields.One2many('hr.overtime', 'batch_id', string='Overtimes',
											copy=True)
	company_id = fields.Many2one('res.company', string='Company', readonly=True,
								 required=True, default=lambda self: self.env.user.company_id.id)

	company_overtime_type = fields.Selection([('payroll', 'Through Payroll'), ('receipt', 'Through Receipt')],
											 related='company_id.overtime_type')

	overtime_website_description = fields.Html('Body Template', sanitize_attributes=False,
											   translate=html_translate, compute='get_overtime_website_description')
	overtime_template_id = fields.Many2one('mail.template', string='overtime Template',
										   related='company_id.overtime_template_id')
	mail_track = fields.Many2one('mail.message', string="Mail tracking")

	@api.depends('overtime_template_id', 'overtime_template_id.body_html')
	def get_overtime_website_description(self):
		"""
		A method to create overtime website description template.
		"""
		for rec in self:
			rec.overtime_website_description += rec.overtime_website_description
			if rec.overtime_template_id and rec.id:
				fields = ['body_html']
				template_values = rec.overtime_template_id.generate_email([rec.id], fields=fields)
				print("template_values", template_values)
				rec.overtime_website_description = template_values[rec.id].get('body_html')

	state = fields.Selection([
		('draft', 'Draft'),

		('confirm', 'Confirmed'),
		('approve', 'Approved'),
		('cancel', 'Cancel'),
	], string='State', readonly=True, default='draft')
	move_ids = fields.Many2many('account.move', string='Recipts', readonly=True, copy=False)

	def action_get_move_ids(self):
		return {
			'name': _('Recipts'),
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', self.move_ids.ids)],
		}

	def action_draft(self):
		"""
		A method to set batch overtime draft.
		"""
		self.write({'state': 'draft'})
		if self.employee_overtime_ids:
			self.employee_overtime_ids.action_submit()

	def action_cancel(self):
		"""
		A method to cancel batch overtime.
		"""
		if self.move_ids:
			for rec in self:
				if rec.move_ids.filtered(lambda r: r.state not in ['draft', 'cancel']):
					raise ValidationError(_("cancel the receipt or delete it before cancel!"))
				elif rec.move_ids.filtered(lambda r: r.state in ['draft']):
					rec.move_ids.filtered(lambda r: r.state in ['draft']).unlink()
				else:
					rec.move_ids.button_cancel()
				rec.write({'state': 'cancel'})

				if rec.employee_overtime_ids:
					rec.employee_overtime_ids.action_cancel()

		else:
			self.employee_overtime_ids.write({'state': 'cancel', 'move_id':False})
			self.write({'state': 'cancel'})

	def action_confirm(self):
		"""
		A method to confirm batch overtime.
		"""
		self.write({'state': 'confirm'})
		if self.employee_overtime_ids:
			self.employee_overtime_ids.action_submit()

	def action_approve(self):
		"""
		A method to approve batch overtime.
		"""
		if self.company_id.overtime_type == 'receipt':
			if not self.company_id.journal_id:
				raise UserError(_("You should configure the 'Overtime Journal' in the HR settings."))
			if not self.company_id.account_id:
				raise UserError(_("You should configure the 'Overtime Account' in the accounting settings."))
			result = self.env['hr.overtime'].read_group([('batch_id', '=', self.id)], ['bank_id'], ['bank_id'])
			for rec in result:
				recipt_lines = []
				lines = self.env['hr.overtime'].search(rec['__domain'])
				for employee in lines.mapped('employee_id'):
					total = 0.0
					filtered_lines = lines.filtered(lambda lin: lin.employee_id.id == employee.id)
					for line in filtered_lines:
						total += line.total_amount
					name = self.name or " "
					recipt_lines.append((0, 0, {
						'name': ' Overtime Of Batch ' + name,
						'account_id': self.company_id.account_id.id,
						'price_unit': total,
						'quantity': 1,
					}))
				vals = {
					'name': '/',
					'partner_id': self.company_id.overtime_partner_id and self.company_id.overtime_partner_id.id or False,
					'ref': 'Overtime of ' + self.sequence,
					'invoice_origin': self.sequence,
					'company_id': self.company_id.id,
					'journal_id': self.company_id.journal_id.id,
					'move_type': 'in_receipt',
					'invoice_line_ids': recipt_lines,
				}
				move_id = self.env['account.move'].sudo().create(vals)
				self.move_ids += move_id
		self.employee_overtime_ids.write({'state': 'approve'})
		self.write({'state': 'approve'})

	def action_fetch(self):
		"""
		A method to get batch overtime within specific period.
		"""
		overtime_ids = self.env['hr.overtime'].search([('start_date', '>=', self.start_date), ('state', '=', 'submit'), \
													   ('end_date', '<=', self.end_date),('batch_id','=',False)]).ids or []
		if overtime_ids:
			for rec in overtime_ids:
				self.write({'employee_overtime_ids': [(4, rec)]})

	@api.model
	def create(self, vals):
		"""
		A method to create batch overtime sequence.
		"""
		seq = self.env['ir.sequence'].next_by_code('batch.sequence') or '/'
		vals['sequence'] = seq
		res = super(OverTimeBatch, self).create(vals)

		return res

	@api.depends('overtime_template_id', 'overtime_template_id.body_html')
	def get_overtime_template(self):
		"""
		A method to create batch overtime template.
		"""
		for res in self:
			overtime_template_id = False
			if res.overtime_template_id:
				overtime_template_id = res.overtime_template_id
				res.get_template(overtime_template_id)

	def unlink(self):
		"""
		A method to delete batch overtime.
		"""
		for overtime_batch in self:
			if overtime_batch.state not in ('draft',):
				raise UserError(_('You can not delete record not in draft state.'))
		return super(OverTimeBatch, self).unlink()

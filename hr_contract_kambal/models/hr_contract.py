# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.tools import float_round, date_utils, convert_file, html2plaintext
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.tools.translate import html_translate
from . import amount_to_ar
from calendar import monthrange
from datetime import datetime , timedelta

class HrEmployee(models.Model):
	_inherit = "hr.employee"

	emp_id = fields.Char()
	bank_id = fields.Many2one('res.bank', related='bank_account_id.bank_id', readonly=False,store=True) 
	home_address = fields.Char("Home Address")
	social_insurance_no = fields.Char()
	religion = fields.Selection(string='Religion', selection=[
		('islam', 'Islam'),
		('christianity', 'Christianity'),
		('other', 'Other')
	])
	have_car = fields.Boolean(default=False)
	have_linces = fields.Boolean(default=False)
	# @api.model
	# def create(self, values):
	# 	values['emp_id'] = self.env['ir.sequence'].get('hr.employee') or '/'
	# 	res = super(HrEmployee, self).create(values)
	# 	return res

class hr_contract_history(models.Model):
	_inherit = 'hr.contract.history'

	state = fields.Selection(selection_add=[
		('wait_hr_approve', 'Waiting HR Approval'),
		('wait_gm_approve', 'Waiting GM Approval'),
	])

class HrContract(models.Model):
	_inherit = "hr.contract"

	# def _get_structure(self):
	# 	if self.company_id.id == self.env.ref('base_custom.alwatania_company').id:
	# 		return self.env.ref('hr_contract_kambal.structure_alwatania_contrect_details').id
	# 	elif self.company_id.id == self.env.ref('base_custom.aldowlia_company').id:
	# 		return self.env.ref('hr_contract_kambal.structure_aldowlia_contrect_details').id
	# 	elif self.company_id.id == self.env.ref('base_custom.ajwaa_company').id:
	# 		return self.env.ref('hr_contract_kambal.structure_ajwaa_contrect_details').id
	# 	else:
	# 		return self.env.ref('hr_contract_kambal.structure_employee_contrect_details').id

	sequence = fields.Char()
	contract_line_ids = fields.One2many('hr.contract.line','contract_id',readonly=True)
	struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',
								tracking=5, )
	# default=_get_structure
	employee_contract_website_description = fields.Html('Body Template', sanitize_attributes=False,
												   translate=html_translate,
												   compute="get_employee_contract_website_description")
	employee_contract_template_id = fields.Many2one('mail.template', string='Employee Contract Template',
											   related='company_id.employee_contract_template_id')
	wage_in_words = fields.Char(string='Amount in Words', readonly=True, default=False, copy=False,
								  compute='_compute_text', translate=True)
	wage_per_hour = fields.Float(compute="_get_wage_per_hour",store=True)
	has_insurance = fields.Boolean(default=False,string='Have Medical Insurance')
	medical_insurance_ids = fields.One2many('hr.medical.insurance','contract_id')
	insurance_categ_id = fields.Many2one('medical.insurance.category')
	medical_amount = fields.Float('Amount To Deduct')
	no_social = fields.Boolean(default=False,string='Have No Social Insurance')
	bouns = fields.Float()
	bouns_2 = fields.Float()
	state = fields.Selection([
		('draft', 'New'),
		('wait_hr_approve', 'Waiting HR Approval'),
		('wait_gm_approve', 'Waiting GM Approval'),
		('open', 'Running'),
		('close', 'Expired'),
		('cancel', 'Cancelled')
	], string='Status', group_expand='_expand_states', copy=False,
	   tracking=True, help='Status of the contract', default='draft')
	

	@api.onchange('medical_insurance_ids')
	def _get_defualt_amount(self):
		for rec in self:
			if rec.insurance_categ_id:
				rec.medical_insurance_ids.insurance_amount = rec.insurance_categ_id.amount

	@api.depends('wage')
	def _compute_text(self):
		self.wage_in_words = amount_to_ar.amount_to_text_ar(self.wage,'جنيه', 'قرش')

	@api.onchange('structure_type_id')
	def onchange_structure_type(self):
		"""	
		A method to change structure type
		"""
		for record in self:
			if record.structure_type_id:
				return {'domain': {'struct_id': [('id', 'in', record.structure_type_id.struct_ids.ids)]}}

	@api.depends('wage')
	def _get_wage_per_hour(self):
		for rec in self:
			rec.wage_per_hour = 0.0
			if rec.resource_calendar_id:
				# days_no = monthrange(fields.Date.today().year, fields.Date.today().month)[1]
				rec.wage_per_hour = (rec.wage / 30) / rec.resource_calendar_id.hours_per_day
			
	@api.model
	def create(self, values):
		values['sequence'] = self.env['ir.sequence'].get('hr.contract') or '/'
		res = super(HrContract, self).create(values)
		return res

	def compute_rules(self):	
		# delete old contract lines
		self.contract_line_ids.unlink()

		# for rule in self.struct_id.rule_ids:
		lines = [(0, 0, line) for line in self._get_contract_lines()]
		self.write({'contract_line_ids': lines})
		return True

	@api.depends('employee_contract_template_id', 'employee_contract_template_id.body_html')
	def get_employee_contract_website_description(self):
		"""
		A method to create employee contract website description template
		"""
		for rec in self:
			rec.employee_contract_website_description += rec.employee_contract_website_description
			if rec.employee_contract_template_id and rec.id:
				fields = ['body_html']
				template_values = rec.employee_contract_template_id.generate_email([rec.id], fields=fields)
				rec.employee_contract_website_description = template_values[rec.id].get('body_html')


	def _get_contract_lines(self):
		self.ensure_one()

		localdict = self.env.context.get('force_payslip_localdict', None)
		if localdict is None:
			localdict = self._get_localdict()

		rules_dict = localdict['rules'].dict
		result_rules_dict = localdict['result_rules'].dict
		blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

		result = {}
		for rule in self.struct_id.rule_ids:
			localdict.update({
				'result': None,
				'result_qty': 1.0,
				'result_rate': 100,
				'result_name': False
			})

			if rule._satisfy_condition(localdict):
				amount, qty, rate = rule._compute_rule(localdict)
				#check if there is already a rule computed with that code
				previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
				#set/overwrite the amount computed for this rule in the localdict
				tot_rule = amount * qty * rate / 100.0
				localdict[rule.code] = tot_rule
				result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
				rules_dict[rule.code] = rule
				# sum the amount for its salary category
				localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
				# Retrieve the line name in the employee's lang
				employee_lang = self.employee_id.sudo().address_home_id.lang
				# This actually has an impact, don't remove this line
				context = {'lang': employee_lang}
				if localdict['result_name']:
					rule_name = localdict['result_name']
				elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION', 'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
					if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
						if rule.name == "Double Holiday Pay":
							rule_name = _("Double Holiday Pay")
						if rule.struct_id.name == "CP200: Employees 13th Month":
							rule_name = _("Prorated end-of-year bonus")
						else:
							rule_name = _('Basic Salary')
					elif rule.code == "GROSS":
						rule_name = _('Gross')
					elif rule.code == "DEDUCTION":
						rule_name = _('Deduction')
					elif rule.code == "REIMBURSEMENT":
						rule_name = _('Reimbursement')
					elif rule.code == 'NET':
						rule_name = _('Net Salary')
				else:
					rule_name = rule.with_context(lang=employee_lang).name

				# create/overwrite the rule in the temporary results
				result[rule.code] = {
					'sequence': rule.sequence,
					'code': rule.code,
					'name': rule_name,
					'note': html2plaintext(rule.note),
					'salary_rule_id': rule.id,
					'contract_id': localdict['contract'].id,
					'employee_id': localdict['employee'].id,
					'amount': amount,
					'quantity': qty,
					'rate': rate,
					'contract_id': self.id,
				}
		return result.values()


	def _get_localdict(self):
		self.ensure_one()

		employee = self.employee_id
		contract = self

		localdict = {
			**{
				'categories': BrowsableObject(employee.id, {}, self.env),
				'rules': BrowsableObject(employee.id, {}, self.env),
				'employee': employee,
				'contract': contract,
				'result_rules': ResultRules(employee.id, {}, self.env)
			}
		}
		return localdict


	def _get__date(self):
		no_days = 30
		date = fields.Date.today()
		while no_days > 0:
			date += timedelta(days=-1)
			no_days -= 1
		return date

	def _check_contract_end(self):
		date = self._get__date()
		contract_ids = self.env['hr.contract'].search([('date_end', '<=', date)])
		contract_in_trail_period = self.env['hr.contract'].search([('trial_date_end', '<=', date)])
		if contract_ids or contract_in_trail_period:
			self.notification_method(contract_ids,contract_in_trail_period)

	def notification_method(self,contract_ids,contract_in_trail_period):
		if contract_ids:
			for rec in contract_ids:
				message_id = self.env['mail.message'].create({
					'message_type': 'notification',
					'body': 'The contract of (%s) has been end after 30 days.' % (rec.employee_id.name),
					'subject': 'تجديد العقد',
					'model': rec._name,
					'res_id': rec.id,
					'partner_ids': [rec.hr_responsible_id.partner_id.id],
					'author_id': self.env.user.partner_id.id,
					'record_name':'تجديد عقد الموظف (%s)' % (rec.employee_id.name),
				})
				self.env['mail.notification'].create({
					'mail_message_id': message_id.id,
					'res_partner_id': rec.hr_responsible_id.partner_id.id,
					'notification_type': 'inbox',
				})
				print('+++++++++++++++ message send success ####################')

		if contract_in_trail_period:
			for rec in contract_in_trail_period:
				message_id = self.env['mail.message'].create({
					'message_type': 'notification',
					'body': 'The contract trail period of (%s) has been end after 30 days.' % (rec.employee_id.name),
					'subject': 'نهاية الفترة التجريبية',
					'model': rec._name,
					'res_id': rec.id,
					'partner_ids': [rec.hr_responsible_id.partner_id.id],
					'author_id': self.env.user.partner_id.id,
					'record_name':'نهاية الفترة التجريبية للموظف (%s)' % (rec.employee_id.name),
				})
				self.env['mail.notification'].create({
					'mail_message_id': message_id.id,
					'res_partner_id': rec.hr_responsible_id.partner_id.id,
					'notification_type': 'inbox',
				})
				print('+++++++++++++++ message send success ####################')



class InsuranceCateg(models.Model):
	_name = 'medical.insurance.category'

	name = fields.Char(required=True)
	amount = fields.Float(required=True,string='Amount Per Person')


class Insurance(models.Model):
	_name = 'hr.medical.insurance'

	name = fields.Char(required=True)
	type_of_relatives = fields.Selection(selection=[('father','Father'),('mother','Mother'),('husband','Husband'),('wife','Wife')],required=True)
	birth_date = fields.Date()
	gender = fields.Selection(selection=[('male','Male'),('female','Female')],required=True)
	contract_id = fields.Many2one('hr.contract')
	insurance_amount = fields.Float(string='Amount',required=True)
	employee_id = fields.Many2one('hr.employee', string="Employee", related='contract_id.employee_id',store=True)
	department_id = fields.Many2one('hr.department',string='Department',related='contract_id.department_id',store=True)
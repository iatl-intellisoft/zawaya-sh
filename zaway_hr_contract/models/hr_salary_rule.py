# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules


class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'
	_description = 'Salary Rule'

	use_type = fields.Selection(string='Use Type', selection=[('general', 'General'), ('special', 'Special')], default='general')
	
	# inprogress
	def compute_rule_amount(self, emp_id):
		def _sum_salary_rule_category(localdict, category, amount):
			if category.parent_id:
				localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
			localdict['categories'].dict[category.code] = localdict['categories'].dict.get(category.code, 0) + amount
			return localdict
		self.ensure_one()
		rules_dict = {}
		result_amount = 0.0
		payslip = self.env['hr.payslip']

		worked_days_dict = {line.code: line for line in payslip.worked_days_line_ids if line.code}

		employee = emp_id
		if emp_id.active:
			domain = [('employee_id', '=', emp_id.id),
						('state', 'in', ['open', 'offer'])]
		else:
			domain = [('employee_id', '=', emp_id.id)]
		contract = self.env['hr.contract'].search(domain,order = 'date_start desc' ,limit=1)
		if not contract and emp_id.active == True:
			raise ValidationError(_("There is no running contract for this Employee %s.") % (emp_id.name))

		localdict = {
			**{
				'categories': BrowsableObject(employee.id, {}, self.env),
				'rules': BrowsableObject(employee.id, rules_dict, self.env),
				'employee': employee,
				'contract': contract
			}
		}
		# print('localdict', localdict)

		rule_ids = self.env['hr.salary.rule'].search([('struct_id','=',contract.struct_id.id),('sequence','<=',self.sequence)])
		# print('rule_idsrule_idsrule_ids',rule_ids)
		if self and self.id not in rule_ids.ids:
			rule_ids = rule_ids + self
		rules_list = [rule for rule in rule_ids.filtered(lambda r: r.amount_select  == 'code' and 'payslip' not in r.amount_python_compute and 'inputs' not in r.amount_python_compute and 'worked_days' not in r.amount_python_compute or r.amount_select  != 'code')]
		for rule in sorted(rules_list, key=lambda x: x.sequence):
			localdict.update({
				'result': None,
				'result_qty': 1.0,
				'result_rate': 100})
			# print('localdictlocaldictlocaldict',localdict)
			if rule._satisfy_condition(localdict):
				amount, qty, rate = rule._compute_rule(localdict)
				# check if there is already a rule computed with that code
				previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
				# set/overwrite the amount computed for this rule in the localdict
				tot_rule = amount * qty * rate / 100.0
				localdict[rule.code] = tot_rule
				# sum the amount for its salary category
				localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
				# create/overwrite the rule in the temporary results
				# print('sum',localdict)

				if rule.id == self.id:
					result_amount += tot_rule
					break		

			result_amount = localdict[rule.code]
		return result_amount

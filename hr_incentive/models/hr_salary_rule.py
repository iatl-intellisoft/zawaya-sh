
# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=False)

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
        employee = emp_id
        contract = self.env['hr.contract'].search([('employee_id', '=', emp_id.id), ('state', 'in', ['open', 'offer'])],
                                                  limit=1)
        if not contract:
            raise ValidationError(_("There is no running contract for this Employee %s.") % (emp_id.name))

        localdict = {
            **{
                'categories': BrowsableObject(employee.id, {}, self.env),
                'rules': BrowsableObject(employee.id, rules_dict, self.env),
                'employee': employee,
                'contract': contract
            }
        }
        rules_list = self.env['hr.salary.rule']
        rule_ids = self.env['hr.salary.rule'].search([])
        rules_list += rule_ids.filtered(lambda r: ('payslip' not in r.quantity and 'inputs' not in r.quantity and 'worked_days' not in r.quantity) \
            and ( (r.amount_select  == 'percentage' and ('payslip' not in r.amount_percentage_base and 'inputs' not in r.amount_percentage_base and 'worked_days' not in r.amount_percentage_base )) \
                or (r.amount_select  == 'code' and ('payslip' not in r.amount_python_compute and 'inputs' not in r.amount_python_compute and 'worked_days' not in r.amount_python_compute )) \
                    or r.amount_select == 'fix' ))
        for rule in sorted(rules_list, key=lambda x: x.sequence):
            localdict.update({
                'result': None,
                'result_qty': 1.0,
                'result_rate': 100})
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

                if rule.id == self.id:
                    result_amount += tot_rule
        if self.code not in localdict:
            raise ValidationError(_('The salary rule (%s) cannot be computed. Please contact your system administrator.')%(self.code))
        result_amount = localdict[self.code]
        return result_amount

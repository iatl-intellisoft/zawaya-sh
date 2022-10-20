# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Zaway HR Management',
    'version': '15.0.1.0',
    'license': 'LGPL-3',
    'category': 'Human Resources/Employees',
    'sequence': 100,
    'summary': 'Centralize employee information',
    'description': "",
    'depends': [
        'base_custom',
        'hr',
        'hr_contract',
        'hr_payroll',
        'hr_holidays',
        'hr_payroll_custom'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/sequance_data.xml',
        'data/employee_contract_template.xml',
        'data/contract_end_cron.xml',
        'data/salary_details.xml',
        'views/hr_contract_view.xml',
        'views/hr_employee.xml',
        'views/res_config_settings.xml',
        'report/employee_contract_report.xml',
        'report/medical_insurance_report.xml',
        'report/reports.xml',
        'views/salary_rule.xml',
    ],
    'test': [],
    'images': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Zaway HR Holidays',
    'version': '1.1',
    'author': 'IATL-IntelliSoft Software',
    'website': 'http://www.intellisoft.sd',
    'category': 'Human Resources',
    'summary': 'Provide Holidays for Zaway Company',
    'description': "",
    'depends': ['base_custom',
        'hr_holidays','zaway_hr_contract','hr_incentive','hr_loan','account','hr_payroll_custom'
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'data/rule_data.xml',
        'data/sequance.xml',
        'data/leave_certificate_template.xml',
        'data/sick_leave_template.xml',
        'wizard/stop_leave_view.xml',
        'views/leave_view.xml',
        'views/leave_type_view.xml',
        'views/hr_employee.xml',
        'views/res_config_settings.xml',
        'views/sale_time_off_view.xml',
        'report/leave_certificate_report.xml',
        'report/leave_sick_report.xml',
        'report/reports.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

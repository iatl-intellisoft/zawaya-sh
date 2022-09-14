# -*- coding: utf-8 -*-
{
    'name': "HR Overtime",

    'summary': """
       Calculate and Manage Employee Overtime""",

    'description': """
        Calculate and Manage Employee Overtime
    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'category': 'base',
    'version': '0.1',
    'depends': ['hr_contract_kambal','hr_payroll_custom'
               # 'hr_custom', 'hr_contract_custom','hr_payroll_custom'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/multi_company.xml',
        'data/hr_overtime_data.xml',
        'views/hr_overtime_views.xml',
        'views/payslip.xml',
        'views/res_config_settings_views.xml',
        'views/reports.xml',
        'views/overtime_template_report.xml',
        # 'data/overtime_template.xml',
    ],
}
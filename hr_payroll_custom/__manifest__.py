

{
    'name': ' Zaway Payroll Module',
    'author': 'IATL-IntelliSoft Software',
    'website': 'http://www.intellisoft.sd',
    'category': 'Human Resources',
    'images': [],
    'summary': '',
    'description': """ """,

    'depends': ['hr','hr_payroll','hr_contract','base_custom'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/almoshraf_salary_rules.xml',
        'data/alwatania_salary_rules.xml',
        'data/aldowlia_salary_rules.xml',
        'data/ajwaa_salary_rules.xml',
        'wizard/employee_payslip_report.xml',
        'views/hr_payslip_view.xml',
        'report/hr_payslip_report_qweb.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
}


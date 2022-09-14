# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

{
    'name': 'HR Loan',
    'author': "IATL Intellisoft International",
    'website': "http://www.iatl-intellisoft.com",
    'category': 'Human Resource',
    'description': """
	""",

    'depends': ['base_custom','mail','account','hr_payroll','hr_contract_kambal','hr_payroll_custom'],
                # 'hr_custom', 'hr_payroll_custom'],
    'data': [
        'security/Loan_security.xml',
        'security/ir.model.access.csv',
        'data/loan_cron.xml',
        'sequences/hr_loan_sequence.xml',
        'data/batch_sequence.xml',
        'report/loan_report.xml',
        'report/reports.xml',
        'report/salary_advance.xml',
        'report/salary_reports.xml',
        'report/loan_contract_report.xml',
        'views/hr_loan_view.xml',
        'views/hr_payroll_view.xml',
        'views/res_config_settings.xml',
        'views/loan_payment_view.xml',
        'views/loan_postpone_views.xml',
        'views/account_move_views.xml',
        'views/loan_batch_view.xml',
        #'data/loan_payroll.xml',
        'data/loan_template.xml',
        'data/salary_advance_template.xml',
        'data/loan_contract_template.xml',

    ],

    'installable': True,
    'auto_install': False,
}

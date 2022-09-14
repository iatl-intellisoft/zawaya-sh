#######################################################################
#    IATL IntelliSoft Software                                             #
#    Copyright (C) 2017 (<http://iatl-intellisoft.sd>) all rights reserved.#
#######################################################################

{
    'name': 'Zaway Accounting Approval 15',
    'author': "IATL Intellisoft",
    'website': "http://www.iatl-intellisoft.com.com",
    'installable': True,
    'auto_install': False,
    'application': True,
    'description': "A module that customizes the accounting module. Migrated to Odoo 15.",
    'depends': ['hr', 'account', 'account_reports', 'ii_simple_check_management'],
    'category': 'Accounting',
    'version': '15.0',
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'data/load.xml',
        'views/approval_sequence.xml',
        'views/res_currency_view.xml',
        'views/finance_approval_view.xml',
        'views/reports_registration.xml',
        'views/report_finance_approval.xml',
        'views/payment_voucher.xml',
        'views/configuration.xml',
    ],

}

# -*- coding: utf-8 -*-
{
    'name': "Zaway Account Custom",

    'summary': """
        """,

    'description': """
    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'category': 'Sales',
    'depends': ['account','account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_view.xml',
        'report/invoice_report.xml',
        'report/cheque_report_view.xml',
        'wizard/cheque_wizard_view.xml',

    ],
}

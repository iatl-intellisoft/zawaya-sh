# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Zawaya Payment Report',
    'version': '1.1',
    'summary': '  Payment Report',
    'sequence': 13,
    'description': """ Print Zawaya Payment Report""",
    'category': 'Accounting/Accounting',
    'depends': ['base', 'account'],

    'data': [
        'report/payment_report.xml',
        'report/report_voucher_payment.xml',
        'report/report_voucher_receipt.xml',

    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

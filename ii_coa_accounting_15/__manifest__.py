# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Axxa COA Accounting Customization',
    'version': '1.1',
    'summary': 'Accounting Customization',
    'sequence': 10,
    'description': """ Accounting Customization """,
    'category': 'Accounting/Accounting',
    'depends': ['base', 'account'],
    'data': [
        'views/ii_account.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

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
        'hr_loan',
    ],
    'data': [

        'views/hr_loan_view.xml',
    ],
    'test': [],
    'images': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

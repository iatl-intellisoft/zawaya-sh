#######################################################################
#    IATL IntelliSoft Software                                             #
#    Copyright (C) 2017 (<http://iatl-intellisoft.sd>) all rights reserved.#
#######################################################################

{
    'name': 'Zaway Custody Clearance',
    'author': "IATL Intellisoft",
    'website': "http://www.iatl-intellisoft.com.com",
    'description': "A module that allows for custody clearance. Migrated to Odoo 15.",
    'depends': ['account', 'is_accounting_approval_15', 'hr'],
    'category': 'Accounting',
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/clearance_sequence.xml',
        'views/clearance_approval_view.xml',
        'views/report_clearance_approval.xml',
        'views/reports_registration.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

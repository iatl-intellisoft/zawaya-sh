# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Kambal Custody",

    'summary': """
        """,

    'description': """
        
    """,
    'author': "IATL Intellisoft International",
    'website': "http://www.iatl-intellisoft.com",
    'category': 'Accounting',
    'depends': [
        'hr','stock','account','mail','hr_loan',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',  
        'data/sequence.xml',
        'views/custody_request.xml',
        'views/custody_exchange.xml',
        'views/custody_return.xml',
        # 'views/res_config.xml',
        
      
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

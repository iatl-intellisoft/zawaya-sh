# -*- coding: utf-8 -*-
{
    'name': "fixed_bom_line",

    'summary': """
        Fixed Consume QTY of Product in the BoM line""",

    'description': """
       Fixed Consume QTY of Product in the BoM line
    """,

    'author': "IATL Intellisoft",
    'website': "http://www.iatl-intellisoft.com.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Manufacturing',
    'version': '15.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp', ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

# -*- coding: utf-8 -*-
{
    'name': "Zaway MRP Custom",

    'summary': """
        """,

    'description': """
    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'category': 'Manufacturing/Manufacturing',
    'depends': ['mrp','zaway_stock_custom','maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_view.xml',
        'wizard/production_wizard_view.xml',
        'report/production_report_view.xml',

    ],
}

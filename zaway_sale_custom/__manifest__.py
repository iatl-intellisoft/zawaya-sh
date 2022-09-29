# -*- coding: utf-8 -*-
{
    'name': "Zaway Sale Custom",

    'summary': """
        """,

    'description': """
    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'category': 'Sales',
    'depends': ['sale','sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/sale_security.xml',
        'data/service_cron.xml',
        'report/sale_report.xml',
        'views/res_config_settings_views.xml',
        'views/sale_view.xml',
        'views/permission_received_viem.xml',
        'wizard/daily_sales_view.xml',
        'report/daily_sales_view.xml',

    ],
}

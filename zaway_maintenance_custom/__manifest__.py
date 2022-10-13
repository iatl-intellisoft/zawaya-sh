# -*- coding: utf-8 -*-
{
    'name': "Zaway Maintenance Custom",

    'summary': """
        """,

    'description': """
    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'category': 'Manufacturing/Maintenance',
    'depends': ['maintenance','mrp_maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'security/maintenance_group.xml',
        # 'data/service_cron.xml',
        # 'report/sale_report.xml',
        'views/maintenance_equipment_view.xml',
        'views/maintenance_request_view.xml',
        # 'wizard/production_wizard_view.xml',
        'report/maintenance_completion_report.xml',

    ],
}

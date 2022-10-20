# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

{
    'name' : 'HR Penalty',
    'summary': """ """,

    'description': """
    """,

    'author': "IATL Intellisoft International",
    'website': "http://www.iatl-intellisoft.com",
    'category': 'Human Resource',

    'depends':['hr_deduction','zaway_hr_contract'],

    'data' : [
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'data/template.xml',

        'views/hr_penalty_view.xml',
        'views/hr_punishment_view.xml',
        'views/res.config.setting.xml',
        # 'report/report.xml',
        'report/penalty_template.xml',
        'report/report_custom.xml',
        'wizard/penalty_cancel_wizard.xml'
    
    ],

    'installable':True,
    'auto_install':False,
}


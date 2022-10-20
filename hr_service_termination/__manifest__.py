# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

{
    'name': "Service Termination",

    'author': "IATL Intellisoft International",
    'website': "http://www.iatl-intellisoft.com",
    'category': 'Human Resource',

    # any module necessary for this one to work correctly
    'depends': ['zaway_hr_contract','hr_payroll','hr_payroll_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'sequences/service_termination_seq.xml',
        'views/hr_payslip.xml',
        'views/hr_contract.xml',
        'views/service_termination_reasons.xml',
        'views/service_termination.xml',
        'views/res_config_settings.xml',
        'views/report_service_termination.xml',
        'views/reports.xml',
        'data/service_termination_template.xml',
    ],
    
}

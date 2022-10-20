# -*- coding: utf-8 -*-
{
    'name': "HR Service Termination Custom",

    'summary': """
        """,

    'description': """

    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'category': 'Human Resource',
    'depends': ['hr_service_termination', 'hr_deduction',
                'hr_incentive','hr_loan','zaway_hr_holidays','ii_custody'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_service_termination_views.xml',
        'views/hr_deduction.xml',
        'views/hr_incentive.xml',
        'views/hr_leave_type_views.xml',
        'views/hr_contract.xml'
    ],
}

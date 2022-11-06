# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

{
    'name': "Zaway Temporary Service Payment",

    'summary': """
	           Pay temporary labor wages through Voucher
    """,

    'description': """

    """,

    'author': "IATL Intellisoft International",
    'website': "http://www.iatl-intellisoft.com",
    'category': 'Human Resource',
    'version': '0.1',
    'depends': ['hr', 'account','is_accounting_approval_15'],
    'data': [
        'security/hr_temporary_service_security.xml',
        'security/ir.model.access.csv',

        'data/temporary_service_data.xml',
        'wizard/hr_partener_service.xml',
        'views/hr_temporary_service_view.xml',
        # 'views/temporary_service_config_view.xml',
        'views/hr_temporary_service_custom_view.xml',
        'views/hr_temporary_service_attendance.xml',
    ],
}

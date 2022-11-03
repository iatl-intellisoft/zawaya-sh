# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2020-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################
{
    'name': 'Account Payment - Change Currency Rate',
    'version': '13.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Allows to change currency of payment',
    'author': 'IATL International',
    'website': 'http://www.iatl-sd.com',
    'depends': ['ii_journal_entry_change_currency_rate'],
    'data': [
        'views/account_payment.xml',
        'views/account_register_payment.xml',
    ],
    "installable": True
}

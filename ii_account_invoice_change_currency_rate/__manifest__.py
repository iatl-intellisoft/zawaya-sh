# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#    Copyright (C) 2020-TODAY Tech-Receptives(<http://www.iatl-sd.com>).
#
###############################################################################
{
    'name': 'Account Invoice - Change Currency Rate',
    'version': '13.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Allows to change currency of invoice',
    'author': 'IATL International',
    'website': 'http://www.iatl-sd.com',
    'depends': ['ii_journal_entry_change_currency_rate'],
    'data': [
        'views/account_invoice.xml',
    ],
    "installable": True
}

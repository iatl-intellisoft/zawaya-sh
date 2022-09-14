{
    'name': 'Accounting US Customizations',
    'version': '1.0',
    'author': 'IATL IntelliSoft',
    'description': """ Customizations to cover currency devaluation in Sudan.""",
    'depends': ['base', 'contacts', 'sale', 'account', 'account_reports'],
    'data': [
        'security/security_view.xml',
        'data/account_financial_report_data.xml',
        'views/ii_accounting_view.xml',
    ],
    'application': True,
}

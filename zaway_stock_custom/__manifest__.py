# -*- coding: utf-8 -*-
{
    'name': "Zaway Inventory Custom",

    'summary': """
        """,

    'description': """
    """,

    'author': "IATL International",
    'website': "http://www.iatl-sd.com",
    'category': 'Inventory/Inventory',
    'depends': ['stock','sale_stock'],
    'data': [

        'security/stock_group.xml',
        'views/product_view.xml',
        'views/stock_view.xml',
        'report/raw_material_recall_order.xml',
        'report/raw_receipt_order.xml',
        'report/products_shipping_order.xml',

    ],
}

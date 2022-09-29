# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "Purchase Request",
    "author": "Iatl_intellisoft",
    "version": "14.0.1.0.0",
    "summary": "Use this module to have notification of requirements of "
               "materials and/or external services and keep track of such "
               "requirements.",
    "website": "https://github.com/OCA/purchase-workflow",
    "category": "Purchase Management",
    "depends": ["purchase", "product", "purchase_stock", "hr", "purchase_requisition"],
    "data": [
        "security/purchase_request.xml",
        "security/ir.model.access.csv",
        "data/purchase_request_sequence.xml",
        'reports/header_footer.xml',
        "reports/purchase_by_quantity_report.xml",
        "reports/print_purchase_request.xml",
        "reports/purchase_by_vendor_report.xml",
        'reports/purchase_received_from_vendor_report.xml',
        'wizard/purchase_by_quantity_wiz.xml',
        'wizard/purchase_by_vendor_wiz.xml',
        'wizard/purchase_received_from_vendor_wiz.xml',
        "views/purchase_request_report.xml",
        "views/purchase_request_view.xml",
        "views/purchase_order_view.xml",
    ],

    "license": "LGPL-3",
    "installable": True,
    "application": True,
}

# -*- coding: utf-8 -*-
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class PurchaseReceivedFromVendor(models.TransientModel):
    _name = 'purchase.received.vendor.wiz'

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    date = fields.Date(string="date", default=fields.Date.context_today)

    def print_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'vendor_name': self.vendor_id.name,
                'vendor_id': self.vendor_id.id,
                'from_date': self.from_date,
                'to_date': self.to_date,
                'date': self.date,
            },
        }

        if data['form']['from_date'] > data['form']['to_date']:
            raise UserError(_("You must be enter start date less than end date !"))
        return self.env.ref('purchase_request.report_purchase_received_vendor_id').report_action([], data=data)


class PurchaseVendorReceivedReport(models.AbstractModel):
    _name = 'report.purchase_request.template_purchase_received_vendor'

    @api.model
    def _get_report_values(self, docids, data=None):
        permission_num = []
        vendor_name = data['form']['vendor_name']
        vendor_id = data['form']['vendor_id']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        date = data['form']['date']
        list_data = []
        partner_dict = {}
        partner_bank = {}
        if from_date and to_date and vendor_id:
            list_data = []
            purchase = self.env['purchase.order'].search(
                [('date_approve', '>=', from_date), ('date_approve', '<=', to_date),
                 ('partner_id', '=', vendor_id), ])
            for rec in purchase:
                for line in rec.order_line:
                    partner_dict[line.product_id.name] = []
                    inventory_list = self.env['stock.picking'].search(
                        [('scheduled_date', '>=', from_date), ('scheduled_date', '<=', to_date),
                         ('purchase_id', '=', rec.id)])
                    for order in inventory_list:
                        partner_dict[line.product_id.name].append([
                            order.name, line.product_qty, line.qty_received, line.product_uom.name,
                            line.price_unit, line.price_subtotal
                        ])

        return {
            'partner_bank': partner_bank,
            'partner_dict': partner_dict,
            'date': date,
            'doc_ids': docids,
            'from_date': from_date,
            'to_date': to_date,
            'vendor_name': vendor_name,
            'vendor_id': vendor_id,
            'docs': list_data,
            'permission_num': permission_num,

        }

# -*- coding: utf-8 -*-
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class PurchaseVendor(models.TransientModel):
    _name = 'purchase.vendor.wiz'

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    date = fields.Date(string="date", default=fields.Date.context_today)

    def print_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'vendor_id': self.vendor_id.name,
                'from_date': self.from_date,
                'to_date': self.to_date,
                'date': self.date,
            },
        }
        if data['form']['from_date'] > data['form']['to_date']:
            raise UserError(_("You must be enter start date less than end date !"))
        return self.env.ref('purchase_request.report_purchase_vendor_id').report_action([], data=data)


class PurchaseVendorReport(models.AbstractModel):
    _name = 'report.purchase_request.template_purchase_vendor'

    @api.model
    def _get_report_values(self, docids, data=None):
        global pay_type, pay_bank
        permission_num = []
        vendor_id = data['form']['vendor_id']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        date = data['form']['date']
        pay_cash = ''
        pay_bank = ''
        list_data = []
        partner_dict = {}
        partner_bank = {}
        if from_date and to_date and vendor_id:
            list_data = []
            purchase = self.env['purchase.order'].search(
                [('date_approve', '>=', from_date), ('date_approve', '<=', to_date),
                 ('partner_id', '=', vendor_id), ])
            invoice = self.env['account.move'].search([])
            for rec in purchase:
                partner_dict[rec.name] = []
                partner_bank[rec.name] = []
                for inv in rec.invoice_ids.filtered(lambda r: r.state == 'posted'):
                    payment = self.env['account.payment'].search(
                        [('ref', '=', inv.name), ('state', '=', 'posted'), ])
                    for pay in payment:
                        if pay.journal_id.type == 'cash':
                            pay_cash = pay.journal_id.type
                            inventory_list = self.env['stock.picking'].search(
                                [('scheduled_date', '>=', from_date), ('scheduled_date', '<=', to_date),
                                 ('purchase_id', '=', rec.id)])
                            for order in inventory_list:
                                for line in rec.order_line:
                                    partner_dict[rec.name].append([
                                        line.product_id.name, order.name, line.product_qty, line.product_uom.name,
                                        line.price_unit, line.price_subtotal,
                                    ])
                        print('LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL', partner_dict)
                        if pay.journal_id.type == 'bank':
                            pay_bank = pay.journal_id.type
                            inventory_list = self.env['stock.picking'].search(
                                [('scheduled_date', '>=', from_date), ('scheduled_date', '<=', to_date),
                                 ('purchase_id', '=', rec.id)])
                            for order in inventory_list:
                                for line in rec.order_line:
                                    partner_bank[rec.name].append([
                                        line.product_id.name, order.name, line.product_qty, line.product_uom.name,
                                        line.price_unit, line.price_subtotal,
                                    ])
                        print(partner_dict, 'BBBBBBBBBBBBBBBBBBBBBBBBBB')
        return {
            'partner_bank': partner_bank,
            'partner_dict': partner_dict,
            'pay_cash': pay_cash,
            'pay_bank': pay_bank,
            'date': date,
            'doc_ids': docids,
            'from_date': from_date,
            'to_date': to_date,
            'vendor_id': vendor_id,
            'docs': list_data,
            'permission_num': permission_num,

        }

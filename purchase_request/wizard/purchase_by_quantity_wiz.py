# -*- coding: utf-8 -*-
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class PurchaseQuantity(models.TransientModel):
    _name = 'purchase.quantity.wiz'

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    product_ids = fields.Many2many('product.product', string='product')

    def print_report(self):
        data = {
            'model': self._name,
            'ids': self.ids,
            'form': {
                'product_ids': self.product_ids.ids,
                'from_date': self.from_date,
                'to_date': self.to_date,
            },
        }
        if data['form']['from_date'] > data['form']['to_date']:
            raise UserError(_("You must be enter start date less than end date !"))
        return self.env.ref('purchase_request.report_purchase_quantity_id').report_action(self, data=data)


class PurchaseQuantityReport(models.AbstractModel):
    _name = 'report.purchase_request.template_purchase_quantity'

    @api.model
    def _get_report_values(self, docids, data=None):
        product_ids = data['form']['product_ids']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        data_list = []
        partner_dict = {}
        partner_search = self.env['res.partner'].search([])
        if from_date and to_date and not product_ids:
            for partner in partner_search:
                partner_dict[partner.name] = []
                data_list = self.env['purchase.order.line'].search(
                    [('order_id.date_approve', '>=', from_date), ('order_id.date_approve', '<=', to_date),
                     ('order_id.partner_id', '=', partner.id),
                     ])
                for rec in data_list:
                    partner_dict[partner.name].append(
                        [rec.order_id.id, rec.order_id.date_approve, rec.price_unit,
                         rec.product_qty, rec.price_subtotal, rec.product_id.name])
            print(partner_dict, 'PPPPPPPPPPPPPPP')

        if from_date and to_date and product_ids:
            data_list = self.env['purchase.order.line'].search(
                [('order_id.date_approve', '>=', from_date), ('order_id.date_approve', '<=', to_date),
                 ('product_id', '=', product_ids)])

        return {
            'doc_ids': docids,
            'from_date': from_date,
            'to_date': to_date,
            'product_ids': product_ids,
            'docs': data_list,
            'partner_dict': partner_dict,

        }

# -*- coding: utf-8 -*-
import json

from odoo import api, models, _
from odoo.tools import float_round

class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    @api.model
    def get_byproducts(self, bom_id=False, qty=0, level=0, total=0):
        bom = self.env['mrp.bom'].browse(bom_id)
        lines, dummy = self._get_byproducts_lines(bom, qty, level, total)
        values = {
            'bom_id': bom_id,
            'currency': self.env.company.currency_id,
            'byproducts': lines,
        }
        return self.env.ref('mrp_custom.report_mrp_byproduct_line')._render({'data': values})

    def _get_bom(self, bom_id=False, product_id=False, line_qty=False, line_id=False, level=False):
        lines = super()._get_bom(bom_id, product_id, line_qty, line_id, level)
        byproducts, byproduct_cost_portion = self._get_byproducts_lines(lines['bom'], lines['bom_qty'], level, lines['total'])
        cost_share = float_round(1 - byproduct_cost_portion, precision_rounding=0.0001)
        lines.update({'byproducts': byproducts,
                      'cost_share': cost_share,
                      'bom_cost': lines['total'] * cost_share,
                      'byproducts_cost': sum(byproduct['bom_cost'] for byproduct in byproducts),
                      'byproducts_total': sum(byproduct['product_qty'] for byproduct in byproducts)})
        return lines

    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        components, total = super()._get_bom_lines(bom, bom_quantity, product, line_id, level)
        for component in components:
            line = bom.bom_line_ids.filtered(lambda l: l.id == component['line_id'])
            byproduct_cost_share = sum(line.child_bom_id.byproduct_ids.mapped('cost_share'))
            if byproduct_cost_share:
                total *= float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001)
        return components, total

    def _get_price(self, bom, factor, product):
        price = super()._get_price(bom, factor, product)
        for line in bom.bom_line_ids:
            if line.child_bom_id:
                byproduct_cost_share = sum(line.child_bom_id.byproduct_ids.mapped('cost_share'))
                if byproduct_cost_share:
                    price *= float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001)
        return price

    def _get_byproducts_lines(self, bom, bom_quantity, level, total):
        byproducts = []
        byproduct_cost_portion = 0
        company = bom.company_id or self.env.company
        for byproduct in bom.byproduct_ids:
            line_quantity = (bom_quantity / (bom.product_qty or 1.0)) * byproduct.product_qty
            cost_share = byproduct.cost_share / 100
            byproduct_cost_portion += cost_share
            price = byproduct.product_id.uom_id._compute_price(byproduct.product_id.with_company(company).standard_price, byproduct.product_uom_id) * line_quantity
            byproducts.append({
                'product_id': byproduct.product_id,
                'product_name': byproduct.product_id.display_name,
                'product_qty': line_quantity,
                'product_uom': byproduct.product_uom_id.name,
                'product_cost': company.currency_id.round(price),
                'parent_id': bom.id,
                'level': level or 0,
                'bom_cost': company.currency_id.round(total * cost_share),
                'cost_share': cost_share,
            })
        return byproducts, byproduct_cost_portion

    def _get_pdf_line(self, bom_id, product_id=False, qty=1, child_bom_ids=[], unfolded=False):
        data = super()._get_pdf_line(bom_id, product_id, qty, child_bom_ids, unfolded)
        lines = data['lines'] or []
        if data['byproducts']:
            level = 1
            lines.append({
                'name': _('Byproducts'),
                'type': 'byproduct',
                'uom': False,
                'quantity': data['byproducts_total'],
                'bom_cost': data['byproducts_cost'],
                'level': level,
            })
            for byproduct in data['byproducts']:
                if unfolded or 'byproduct-' + str(bom_id) in child_bom_ids:
                    lines.append({
                        'name': byproduct['product_name'],
                        'type': 'byproduct',
                        'quantity': byproduct['product_qty'],
                        'uom': byproduct['product_uom'],
                        'prod_cost': byproduct['product_cost'],
                        'bom_cost': byproduct['bom_cost'],
                        'level': level + 1,
                    })
        return data

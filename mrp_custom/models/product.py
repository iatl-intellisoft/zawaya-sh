# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_bom_price(self, bom, boms_to_recompute=False):
        total = super()._compute_bom_price(bom, boms_to_recompute)
        byproduct_cost_share = sum(bom.byproduct_ids.mapped('cost_share'))
        if byproduct_cost_share:
            total *= float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001)
        return total

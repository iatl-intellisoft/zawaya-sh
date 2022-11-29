# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime


class MrpByProduct(models.Model):
    _inherit = 'mrp.bom.byproduct'

    cost_share = fields.Float(
        "Cost Share (%)", digits=(5, 2),  # decimal = 2 is important for rounding calculations!!
        help="The percentage of the final production cost for this by-product line (divided between the quantity produced)."
             "The total of all by-products' cost share must be less than or equal to 100.")
    have_cost = fields.Boolean("Have a Cost", default=True)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.constrains('byproduct_ids')
    def check_cost_share(self):
        for bom in self:
            for byproduct in bom.byproduct_ids:
                if byproduct.cost_share < 0:
                    raise ValidationError(_("By-products cost shares must be positive."))
            if sum(bom.byproduct_ids.mapped('cost_share')) > 100:
                raise ValidationError(_("The total cost share for a BoM's by-products cannot exceed 100."))

    fix_product = fields.Many2one('product.product', 'Fix Product')
    share_costing_method = fields.Selection([('consume_cost_share', 'Cost Share base on Produce QTY'), ('formula_cost_share', 'Cost Share base on Formula'), ('cost_share', 'Cost Share')], 'Share Costing Method',)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    share_costing_method = fields.Selection('Share Costing Method', related='bom_id.share_costing_method', store=True)
    fix_product = fields.Many2one('product.product', 'Fix Product' , related='bom_id.fix_product', store=True)
    fix_product_cost = fields.Float('Fix Product Cost' , related='bom_id.fix_product.standard_price', store=True)

    @api.constrains('move_byproduct_ids')
    def _check_byproducts(self):
        for order in self:
            if any(move.cost_share < 0 for move in order.move_byproduct_ids):
                raise ValidationError(_("By-products cost shares must be positive."))
            if sum(order.move_byproduct_ids.mapped('cost_share')) > 100:
                raise ValidationError(_("The total cost share for a manufacturing order's by-products cannot exceed 100."))

    def _get_move_finished_values(self, product_id, product_uom_qty, product_uom, operation_id=False, byproduct_id=False):
        res = super(MrpProduction, self)._get_move_finished_values(product_id, product_uom_qty, product_uom, operation_id, byproduct_id)
        byproduct = self.env['mrp.bom.byproduct'].browse(res['byproduct_id'])
        if byproduct and byproduct.cost_share:
            res.update({'cost_share': byproduct.cost_share})
        else:
            res.update({'cost_share': 0})
        if byproduct and byproduct.have_cost:
            res.update({'have_cost': byproduct.have_cost})
        return res

    def _cal_price(self, consumed_moves):
        super(MrpProduction, self)._cal_price(consumed_moves)
        work_center_cost = 0
        qty_consumed = 0
        finished_move = self.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel') and x.quantity_done > 0)
        if finished_move:
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(
                    lambda x: x.date_end and not x.cost_already_recorded)
                duration = sum(time_lines.mapped('duration'))
                time_lines.write({'cost_already_recorded': True})
                work_center_cost += (duration / 60.0) * \
                    work_order.workcenter_id.costs_hour
            qty_done = finished_move.product_uom._compute_quantity(
                finished_move.quantity_done, finished_move.product_id.uom_id)
            for consumed_move in consumed_moves:
                qty_consumed += consumed_move.product_uom._compute_quantity(
                    consumed_move.quantity_done, consumed_move.product_id.uom_id)
            extra_cost = self.extra_cost * qty_done
            total_cost = (sum(-m.stock_valuation_layer_ids.value for m in consumed_moves.sudo()) + work_center_cost + extra_cost)
            byproduct_moves = self.move_byproduct_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.quantity_done > 0)
            byproduct_cost_share = 0
            if self.share_costing_method == 'consume_cost_share' and qty_consumed > 0:
                for byproduct in byproduct_moves:
                    if not byproduct.have_cost:
                        continue
                    byproduct_cost_share = (byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id)/qty_consumed )* 100
                    if byproduct.product_id.cost_method in ('fifo', 'average'):
                        byproduct.price_unit = total_cost * float_round(byproduct_cost_share / 100 , precision_rounding=0.0001) / byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id)
                        byproduct.cost_share = byproduct_cost_share
                if finished_move.product_id.cost_method in ('fifo', 'average'):
                    finproduct_cost_share = (qty_done / qty_consumed )* 100
                    finished_move.cost_share = finproduct_cost_share
                    finished_move.price_unit = total_cost * float_round(finproduct_cost_share / 100, precision_rounding=0.0001) / qty_done
            elif self.share_costing_method == 'formula_cost_share' and qty_consumed > 0:
                byproduct_moves_cost = byproduct_moves.filtered(lambda x: x.have_cost and x.product_id != self.fix_product)
                fix_byproduct_move = byproduct_moves.filtered(lambda x: x.product_id == self.fix_product)
                byproduct_done_qty = sum(byproduct_cost.product_uom._compute_quantity(byproduct_cost.quantity_done, byproduct_cost.product_id.uom_id) for byproduct_cost in byproduct_moves_cost)
                fix_product_tot_cost = (total_cost - (self.fix_product_cost * sum(fix_byproduct_move.mapped('quantity_done')))) / (byproduct_done_qty + qty_done)
                for byproduct in byproduct_moves:
                    if not byproduct.have_cost:
                        continue
                    if byproduct.product_id.cost_method in ('fifo', 'average'):
                        if byproduct.product_id != self.fix_product:
                            byproduct.price_unit = fix_product_tot_cost
                        else:
                            byproduct.price_unit = self.fix_product_cost
                if finished_move.product_id.cost_method in ('fifo', 'average'):
                    finished_move.price_unit = fix_product_tot_cost
            else:
                for byproduct in byproduct_moves:
                    if byproduct.cost_share == 0:
                        continue
                    byproduct_cost_share += byproduct.cost_share
                    if byproduct.product_id.cost_method in ('fifo', 'average'):
                        byproduct.price_unit = total_cost * byproduct.cost_share / 100 / byproduct.product_uom._compute_quantity(
                            byproduct.quantity_done, byproduct.product_id.uom_id)
                if finished_move.product_id.cost_method in ('fifo', 'average'):
                    finished_move.price_unit = total_cost * float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001) / qty_done
        return True



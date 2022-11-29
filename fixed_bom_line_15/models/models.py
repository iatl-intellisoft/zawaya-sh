# -*- coding: utf-8 -*-

# from odoo import models, fields, api
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from datetime import timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
import dateutil.parser
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    is_fixed = fields.Boolean(string="Fixed", related='bom_id.fixed')

    def _pre_button_mark_done(self):
        productions_to_immediate = self._check_immediate()
        if productions_to_immediate:
            return productions_to_immediate._action_generate_immediate_wizard()

        for production in self:
            if float_is_zero(production.qty_producing, precision_rounding=production.product_uom_id.rounding):
                raise UserError(_('The quantity to produce must be positive!'))
            if not any(production.move_raw_ids.mapped('quantity_done')):
                raise UserError(_("You must indicate a non-zero amount consumed for at least one of your components"))
        if not self.is_fixed:
            consumption_issues = self._get_consumption_issues()
            if consumption_issues:
                return self._action_generate_consumption_wizard(consumption_issues)

        quantity_issues = self._get_quantity_produced_issues()
        if quantity_issues:
            return self._action_generate_backorder_wizard(quantity_issues)
        return True

    def _set_qty_producing(self):
        if self.product_id.tracking == 'serial':
            qty_producing_uom = self.product_uom_id._compute_quantity(self.qty_producing, self.product_id.uom_id,
                                                                      rounding_method='HALF-UP')
            if qty_producing_uom != 1:
                self.qty_producing = self.product_id.uom_id._compute_quantity(1, self.product_uom_id,
                                                                              rounding_method='HALF-UP')

        for move in (self.move_raw_ids | self.move_finished_ids.filtered(lambda m: m.product_id != self.product_id)):
            if move._should_bypass_set_qty_producing() or not move.product_uom:
                continue
            if self.is_fixed == False:
                new_qty = float_round((self.qty_producing - self.qty_produced) * move.unit_factor,
                                      precision_rounding=move.product_uom.rounding)
                move.move_line_ids.filtered(lambda ml: ml.state not in ('done', 'cancel')).qty_done = 0
                move.move_line_ids = move._set_quantity_done_prepare_vals(new_qty)
            else:
                new_qty = float_round(self.product_qty * move.unit_factor,
                                      precision_rounding=move.product_uom.rounding)
                move.move_line_ids.filtered(lambda ml: ml.state not in ('done', 'cancel')).qty_done = 0
                move.move_line_ids = move._set_quantity_done_prepare_vals(new_qty)

    # def _get_moves_finished_values(self):
    #     moves = []
    #     for production in self:
    #         if production.product_id in production.bom_id.byproduct_ids.mapped('product_id'):
    #             raise UserError(
    #                 _("You cannot have %s  as the finished product and in the Byproducts", self.product_id.name))
    #         moves.append(production._get_move_finished_values(production.product_id.id, production.product_qty,
    #                                                           production.product_uom_id.id))
    #         for byproduct in production.bom_id.byproduct_ids:
    #             if byproduct.fixed:
    #                 qty = byproduct.product_qty
    #             else:
    #                 product_uom_factor = production.product_uom_id._compute_quantity(production.product_qty,
    #                                                                                  production.bom_id.product_uom_id)
    #                 qty = byproduct.product_qty * (product_uom_factor / production.bom_id.product_qty)
    #             moves.append(production._get_move_finished_values(
    #                 byproduct.product_id.id, qty, byproduct.product_uom_id.id,
    #                 byproduct.operation_id.id, byproduct.id))
    #     return moves

    # def _get_moves_raw_values(self):
    #     moves = []
    #     for production in self:
    #         factor = production.product_uom_id._compute_quantity(production.product_qty,
    #                                                              production.bom_id.product_uom_id) / production.bom_id.product_qty
    #         boms, lines = production.bom_id.explode(production.product_id, factor,
    #                                                 picking_type=production.bom_id.picking_type_id)
    #         for bom_line, line_data in lines:
    #             if bom_line.fixed:
    #                 if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or \
    #                         bom_line.product_id.type not in ['product', 'consu']:
    #                     continue
    #                 operation = bom_line.operation_id.id or line_data['parent_line'] and line_data[
    #                     'parent_line'].operation_id.id
    #                 moves.append(production._get_move_raw_values(
    #                     bom_line.product_id,
    #                     bom_line.product_qty,
    #                     bom_line.product_uom_id,
    #                     operation,
    #                     bom_line
    #                 ))
    #             else:
    #                 if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or \
    #                         bom_line.product_id.type not in ['product', 'consu']:
    #                     continue
    #                 operation = bom_line.operation_id.id or line_data['parent_line'] and line_data[
    #                     'parent_line'].operation_id.id
    #                 moves.append(production._get_move_raw_values(
    #                     bom_line.product_id,
    #                     line_data['qty'],
    #                     bom_line.product_uom_id,
    #                     operation,
    #                     bom_line
    #                 ))
    #     return moves


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    fixed = fields.Boolean(string='Fixed')


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    fixed = fields.Boolean(string='Fixed')


class MrpBomByproduct(models.Model):
    _inherit = 'mrp.bom.byproduct'

    fixed = fields.Boolean(string='Fixed')

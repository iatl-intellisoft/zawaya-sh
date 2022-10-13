# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL International Pvt. Ltd.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare
import math
import babel
import time
from odoo import tools


class StockMove(models.Model):
    _inherit = 'stock.move'

    thickness = fields.Float(string="Thickness",related="product_id.thickness")
    # package_domain = fields.Many2many('stock.quant.package','stock_quant_package_rel', 'domain_id', 'package_id',string="Package", compute='_compute_package',readonly=False,store=True)
    # packag_product = fields.Many2many('stock.quant.package','stock_package_rel', 'packag_product_id', 'quant_package_id',string="Package")
    #packag_product = fields.Many2many('stock.quant.package','stock_package_rel', 'packag_product_id', 'quant_package_id',string="Package", domain=lambda self: [('id','=',self.env['stock.quant.package'].search([]).filtered(lambda x: x.quant_ids.product_id == self.product_id.id))])
    
    tape_number = fields.Float(string="Tape Number")
    # count_package = fields.Integer(string="Number of Packages",compute='compute_product_uom_qty')



    # @api.onchange('product_id','raw_material_production_id.product_id')
    # def _compute_package(self):
    #   self.package_domain = None
    #   for rec in self:
    #       package = self.env['stock.quant.package'].search([('quant_ids.product_id','=',rec.product_id.id)])
    #       print("_____________________________",package.ids)
    #       rec.package_domain =  package
    #       return [('packag_product','in',package.ids)]



    # @api.onchange('packag_product','product_id','raw_material_production_id.bom_id')
    # def compute_product_uom_qty(self):
    #     self.product_uom_qty = 0
    #     product_uom_qty_package = 0
    #     count = 0
    #     # self.count_package =len(self.packag_product.quant_ids.filtered(lambda r:r.product_id == self.product_id))
    #     for rec in self.packag_product.quant_ids.filtered(lambda r:r.product_id == self.product_id):
    #         product_uom_qty_package+= rec.quantity
    #         count+= 1 
   
    #     self.write({'product_uom_qty':product_uom_qty_package,'count_package':count})


    # def action_show_details(self):
    #     self.ensure_one()
    #     action = super().action_show_details()
    #     if self.raw_material_production_id:
    #         action['views'] = [(self.env.ref('mrp.view_stock_move_operations_raw').id, 'form')]
    #         action['context']['show_destination_location'] = False
            
    #     elif self.production_id:
    #         action['views'] = [(self.env.ref('mrp.view_stock_move_operations_finished').id, 'form')]
    #         action['context']['show_source_location'] = False

    #     ids = []
    #     for package in self.packag_product:
    #         new_id = self.env['stock.move.line'].create({
    #             'location_id':self.location_id.id,
    #             'package_id':package.id,
    #             'move_id':self.id,
    #             'product_uom_id':self.product_id.uom_id.id
    #         })
    #         ids.append(new_id.id)
    #     self.write({
    #         'move_line_ids':[(6,0,ids)]
    #         })
    #     return action



class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    number_turns = fields.Float(string="Number Of Turns")
    compute_num = fields.Boolean(compute="_compute_unm_package")


    @api.onchange('product_id','bom_id','move_raw_ids')
    def compute_weight_product(self):
        for rec in self.move_raw_ids:
            if rec.product_id.weight_product <= 0:

                rec.product_id.weight_product = rec.product_id.thickness *  rec.product_id.width *  rec.product_id.density * rec.product_id.length


    @api.depends('number_turns')
    def _compute_unm_package(self):
        self.compute_num = False
        for rec in self:
            if rec.number_turns >= 1:
                rec.compute_num = True
            else:
                rec.compute_num = False



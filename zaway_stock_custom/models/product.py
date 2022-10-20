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

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    row_material = fields.Boolean(string="Row Material?")
    qty_package = fields.Float('Package', compute='_compute_package') 
    thickness = fields.Float(string="Thickness")
    width =  fields.Float(string="Width")
    density = fields.Float(string="Density")
    length =fields.Float(string="Length")
    weight_product = fields.Float(string="Weight")
    location_id = fields.Many2one('stock.location',string="Location")
    weight_categ = fields.Boolean(related='categ_id.has_weigth')


    def action_open_quants_pack(self):
        res = super(ProductTemplate, self).action_open_quants()
        return res

    def _compute_package(self):
        self.qty_package = 0
        package = self.env['stock.quant.package'].search([('quant_ids.product_id','=',self.name)])
        for record in self:
            record.qty_package = len(package)




class ProductCategory(models.Model):
    _inherit = 'product.category'

    has_weigth = fields.Boolean(string="Has Weight?")
    location_id = fields.Many2one('stock.location',string="Location")
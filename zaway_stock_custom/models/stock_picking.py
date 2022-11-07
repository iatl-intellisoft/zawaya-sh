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

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # state = fields.Selection(selection_add=[
    #     ('sale','Sale Manger'),
    #     ('wait_it_approve', 'Waiting IT Approval'),
    #     ('wait_manufac_approve', 'Waiting Manufacturer Approval'),
    #     ('wait_gm_approve', 'Stock Manger'),

    # ])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sale','Sale Manger'),
        ('wait_it_approve', 'Waiting IT Approval'),
        ('wait_manufac_approve', 'Waiting Manufacturer Approval'),
        ('wait_gm_approve', 'Stock Manger'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True)


    address = fields.Char(string="Address")
    driver_name = fields.Char(string="Driver's Name")
    forklift_driver = fields.Char(string="Forklift Driver")
    plate_number = fields.Char(string="Plate Number")
    operation_code = fields.Selection([('incoming', 'Receipt'), ('outgoing', 'Delivery'), ('internal', 'Internal Transfer')], 'Type of Operation', related="picking_type_id.code")
    stock_manger_sign = fields.Many2one('res.users')
    it_sign = fields.Many2one('res.users')
    manufac_sign = fields.Many2one('res.users')
    sale_sign = fields.Many2one('res.users')
    check_it =fields.Boolean(defaul=False)

#Date
    stock_manger_date = fields.Date(string="Date")
    it_date = fields.Date(string="Date")
    manufac_date = fields.Date(string="Date")
    sale_date = fields.Date(string="Date")


    def action_sale_manger(self):
        self.write({'state': 'wait_manufac_approve'})
        self.sale_sign = self.env.user
        self.sale_date = fields.date.today()
        self.check_it = True



    def action_manufac_approve(self):
        if self.picking_type_id.code == 'outgoing' and self.sale_id:
            self.write({'state': 'wait_it_approve'})
            self.manufac_sign = self.env.user
            self.manufac_date = fields.date.today()

        else:
            self.write({'state': 'wait_gm_approve'})
            self.manufac_sign = self.env.user
            self.manufac_date = fields.date.today()


    def action_it_approve(self):
        if self.picking_type_id.code == 'outgoing' and self.sale_id:
            self.write({'state': 'wait_gm_approve'})
            self.it_sign = self.env.user
            self.it_date = fields.date.today()

        elif self.picking_type_id.code == 'incoming' and self.purchase_id:
            self.write({'state': 'wait_manufac_approve'})
            self.it_sign = self.env.user
            self.it_date = fields.date.today()

        else:
            self.write({'state': 'wait_manufac_approve'})
            self.it_sign = self.env.user
            self.it_date = fields.date.today()



    def button_validate(self):
        res = super(StockPicking,self).button_validate()
        self.stock_manger_sign = self.env.user.id
        self.stock_manger_date = fields.date.today()
        return res

class StockMoveInheirt(models.Model):
    _inherit = 'stock.move'

    units_sale = fields.Many2one('uom.uom',related='sale_line_id.product_uom', string="Unit Of Sale")
    qty_sale = fields.Float(related='sale_line_id.product_uom_qty',string="Quantity Sale")
    count_package = fields.Float(string="Number Of Package",compute='compute_count_package')

    @api.depends('product_id','product_packaging_id')
    def compute_count_package(self):
        self.count_package = 0

        count = 0
        # self.count_package =len(self.packag_product.quant_ids.filtered(lambda r:r.product_id == self.product_id))
        for rec in self.product_packaging_id:
            count+= 1 
        self.count_package = count


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    pick_components = fields.Boolean(string="Pick Components")

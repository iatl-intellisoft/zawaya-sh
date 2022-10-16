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
from odoo import tools


class MaintenanceRequestInherit(models.Model):
    _inherit = 'maintenance.request'


    department_id = fields.Many2one('hr.department',string='Department',related='employee_id.department_id',store=True)
    spart_line_ids = fields.One2many('spare.parts','order_id',string="Spare Parts")
    description_problem = fields.Html(string="Description Problem")
    Work_required = fields.Html(string="Work Required")
    model = fields.Char(string="Equipment Model", related="equipment_id.model")
    serial_no = fields.Char(string="Equipment Serial", related="equipment_id.serial_no")
    code = fields.Char(string="Equipment Code", related="equipment_id.code")
    manufacture_company = fields.Char(string="Equipment Manufacture Company", related="equipment_id.manufacture_company")
    stock_picking_id= fields.One2many('stock.picking','maintenance_request_id',string="picking")
    check_picking = fields.Boolean(default=False)
    stage_check = fields.Boolean(related="stage_id.in_progress")
    is_requested = fields.Boolean(default=True)
    wait_manger = fields.Boolean(default=False)
    is_approve = fields.Boolean(default=False)
    # state = fields.Selection([
    #     ('draft', 'Waiting Department Manager'),
    #     ('dep_manger','Approved')])

    def action_send_manger(self):
        for rec in self:
            rec.write({'is_requested': False,'wait_manger': True})

    def action_dep_manger(self):
        for rec in self:
            rec.write({'wait_manger': False,'is_approve': True})

    def create_picking(self):
        lines = []
        for line in self.spart_line_ids:
            for operation_type in self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing'),
                 ('company_id', '=', self.env.company.id)],limit=1):
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'location_id': operation_type.default_location_src_id.id,
                    'location_dest_id': operation_type.default_location_dest_id.id,
                    'state': 'draft',
                    'name': self.name,
                    'origin': str(self.name),
                    }))
                vals = {
                    'origin': str(self.name),
                    # 'partner_id': self.customer_id.id,
                    'picking_type_id': operation_type.id,
                    'location_id': operation_type.default_location_src_id.id,
                    'location_dest_id': operation_type.default_location_dest_id.id,
                    'maintenance_request_id': self.id,
                    'move_ids_without_package': lines,
                    }

                picking_id = self.env['stock.picking'].create(vals)
                self.check_picking =True


    def action_view_picking(self):
        self.ensure_one()
        return {
        'type': 'ir.actions.act_window',
        'name': 'Stock',
        'view_mode': 'tree,form',
        'res_model': 'stock.picking',
        'domain': [('maintenance_request_id', '=', self.id)],
        'context': "{'default_maintenance_request_id': active_id,'create': False}"
        }

class SpareParts(models.Model):
    _name = 'spare.parts'

    order_id = fields.Many2one('maintenance.request',string="Maintenance")
    product_id = fields.Many2one('product.product',string="Product")
    uom_id = fields.Many2one('uom.uom',related='product_id.uom_id')
    quantity = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Price")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    maintenance_request_id = fields.Many2one('maintenance.request',string="Maintenance Request")


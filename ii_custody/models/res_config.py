from odoo import fields, models

class ConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',config_parameter='ii_custody.picking_type_id',domain="[('code','=','outgoing')]")

   
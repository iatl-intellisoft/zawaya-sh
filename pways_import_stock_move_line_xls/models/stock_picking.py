# -*- coding: utf-8 -*-
from odoo import models
from odoo import models, fields, exceptions, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_stock_import(self):
        action = self.env.ref('pways_import_stock_move_line_xls.action_stock_import_wizard').read()[0]
        action.update({'views': [[False, 'form']]})
        return action



class stockMoveLineInh(models.Model):
    _inherit  = 'stock.move.line'

    package_name = fields.Char('Package Name')
    package_type = fields.Char()
    package_type_id = fields.Many2one('stock.package.type')

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        if 'move_line_ids' in vals:
            move_line_vals = vals.pop('move_line_ids')
            super().write({'move_line_ids': move_line_vals})
        return super().write(vals)
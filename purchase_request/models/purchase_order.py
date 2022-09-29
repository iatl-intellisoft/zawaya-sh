# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request Ref",track_visibility="onchange")


class PurchaseOrder_r(models.Model):
    _inherit = "purchase.requisition"

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request Ref")
    is_request = fields.Boolean('is Request', default=False)

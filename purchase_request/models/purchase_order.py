# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request Ref",
                                          track_visibility="onchange")
    currency_name = fields.Char(related='currency_id.name', )

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('manager approval', 'Manager Approved'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    def button_manager_approval(self):
        # self.acvtivity_id.unlink()
        pu_group_id = self.env['res.groups'].sudo().search(
            [('id', '=', self.env.ref('purchase_request.group_purchase_manager').id)], limit=1).id
        self.env.cr.execute('''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % (pu_group_id))
        # schedule activity for user(s) to approve
        for fm in list(filter(lambda x: (
                self.env['res.users'].sudo().search([('id', '=', x)]).company_id == self.company_id),
                              self.env.cr.fetchall())):
            vals = {
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', u'To Do')],
                    limit=1).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search(
                    [('model', 'like', 'purchase.order')], limit=1).id,
                'user_id': fm[0] or 2,
                'summary': u'Reminder To Pay Vendor Bill',
            }
            print(vals, 'SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS')
            activity_id = self.env['mail.activity'].sudo().create(vals)
        self.write({"state": "manager approval"})

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True


class PurchaseOrder_r(models.Model):
    _inherit = "purchase.requisition"

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request Ref")
    is_request = fields.Boolean('is Request', default=False)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    company_currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    price_exchange_usd = fields.Float(string='Price in USD', compute='exchange_function')
    price_exchange_sdg = fields.Monetary(string='Price in SDG', currency_field='company_currency_id',
                                         compute='exchange_function')

    @api.depends('product_id')
    def exchange_function(self):
        for rec in self:
            rec.price_exchange_sdg = 0.0
            rec.price_exchange_usd = 0.0
            if rec.order_id.currency_id != rec.company_currency_id:
                currency_rate = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id),
                                                                      ('name', '=', rec.order_id.date_order), ],
                                                                     limit=1)
                for currency in currency_rate:
                    rec.price_exchange_sdg = rec.price_unit * currency.inverse_company_rate
            else:
                currency_rate = self.env['res.currency.rate'].search([('name', '=', rec.order_id.date_order), ],
                                                                     limit=1)
                for currency in currency_rate:
                    rec.price_exchange_usd = rec.price_unit * currency.company_rate

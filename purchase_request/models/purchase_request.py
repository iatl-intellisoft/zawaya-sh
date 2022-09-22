# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_STATES = [
    ("draft", "Draft"),
    ('confirm', 'confirm by Requester'),
    ("direct_manager", "Waiting Direct Manager Approve"),
    ("factory_manager", "Waiting Factory Manager Approve"),
    ("po_create", "PO Created"),
    ("Requisition_create", "Purchase Requisition Created"),
    ("rejected", "Rejected"),
    # ("canceled", "Cancelled"),
    ("done", "Done"),
]


class PurchaseRequest(models.Model):
    _name = "purchase.request"
    _description = "Purchase Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    @api.model
    def _company_get(self):
        return self.env["res.company"].browse(self.env.company.id)

    def _get_default_requested_by(self):
        return self.env["res.users"].browse(self.env.uid)

    @api.depends('user_id')
    def _get_requester(self):
        """
        A method to get Requester
        """
        for rec in self:
            if rec.user_id and rec.id:
                employee = rec.env['hr.employee'].search([('user_id', '=', rec.user_id.id)], limit=1)
                if employee:
                    for record in employee:
                        requester = record.id
                    rec.requested_by = requester or False
                else:
                    rec.requested_by = False

    @api.model
    def create(self, vals):
        res = super(PurchaseRequest, self).create(vals)
        next_seq = self.env['ir.sequence'].get('purchase.request.seq')
        res.update({'name': next_seq})
        return res

    name = fields.Char(string="Request Reference", readonly="1", track_visibility="onchange",
                       states={'done': [('readonly', True)]})
    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    origin = fields.Char(string="Source Document", states={'done': [('readonly', True)]})
    date_start = fields.Date(string="Request date", help="Date when the user initiated the request.",
                             default=fields.Date.context_today, track_visibility="onchange",
                             states={'done': [('readonly', True)]})
    user_id = fields.Many2one(comodel_name="res.users", string="User ", copy=False, tracking=True,
                              default=_get_default_requested_by, index=True, )
    requested_by = fields.Many2one(comodel_name="hr.employee", string="Requested by", compute='_get_requester')
    request_type = fields.Selection([('local', 'Local Request'), ('external', 'External Request')],
                                    string='Request Type', required=True, default='local',
                                    states={'done': [('readonly', True)]})
    last_date = fields.Date('Please provide the above materials no later than')
    # product_type = fields.Selection([('spare', 'Spare Parts'),('vehicle', 'Vehicle'),('other', 'Others')], string='Products Type', required=True, states={'done': [('readonly', True)]})
    vendor_type = fields.Selection([('single', 'Single Source'), ('multi', 'Multi Source')], string='Vendor Type', )

    description = fields.Text(string="Description", states={'done': [('readonly', True)]})
    department_id = fields.Many2one(comodel_name='hr.department', related='requested_by.department_id')
    is_department_manager = fields.Boolean('Is Department Manager', compute='_check_department_manager', store=True)

    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=True, default=_company_get,
                                 track_visibility="onchange", states={'done': [('readonly', True)]})
    line_ids = fields.One2many(comodel_name="purchase.request.line", inverse_name="request_id",
                               string="Products to Purchase", readonly=False, copy=True, track_visibility="onchange",
                               states={'done': [('readonly', True)]})
    state = fields.Selection(selection=_STATES, string="Status", index=True, track_visibility="onchange", required=True,
                             copy=False, default="draft", states={'done': [('readonly', True)]})
    purchase_count = fields.Integer(string="Purchases count", compute='_compute_purchase_count', readonly=True,
                                    states={'done': [('readonly', True)]})
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    Requisition_count = fields.Integer(string="Purchases count", compute='_compute_Requisition_count', readonly=True,
                                       states={'done': [('readonly', True)], 'rejected': [('readonly', True)],
                                               'Requisition_create': [('readonly', True)]})
    activity_id = fields.Many2one('mail.activity', string="Activity")
    requester_sign = fields.Many2one('res.users')
    requester_sign_date = fields.Date()
    datesign = fields.Date(default=fields.Date.context_today, )
    dir_mgn_sign = fields.Many2one('res.users')
    dir_mgn_sign_date = fields.Date()
    factory_sign = fields.Many2one('res.users')
    factory_sign_date = fields.Date()
    gm_sign = fields.Many2one('res.users')
    gm_sign_sign_date = fields.Date()

    def _compute_purchase_count(self):
        for rec in self:
            orders = self.env['purchase.order'].search([('purchase_request_id', '=', rec.id)])
            rec.purchase_count = len(orders)

    def _compute_Requisition_count(self):
        for rec in self:
            orders = self.env['purchase.requisition'].search([('purchase_request_id', '=', rec.id)])
            rec.Requisition_count = len(orders)

    def unlink(self):
        for request in self:
            if request.state != 'draft':
                raise UserError(
                    _("You cannot delete a purchase request which is not draft.")
                )
        return super(PurchaseRequest, self).unlink()

    def button_draft(self):
        if not self.line_ids:
            raise UserError(
                _(
                    "You can't request an approval for a purchase request "
                    "which is empty. (%s)"
                )
                % self.name
            )
        else:
            self.write({"state": 'confirm'})

    # # Notification + status buttons
    def button_confirm(self):
        self.activity_id.unlink()
        if self.env.user.has_group("purchase_request.group_direct_manager"):
            vals = {
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', u'To Do')],
                    limit=1).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search(
                    [('model', '=', 'purchase.request')], limit=1).id,

                'summary': u'This request is delivered',
            }
            activity_id = self.env['mail.activity'].sudo().create(vals)
        self.write({"state": "confirm"})
        self.requester_sign = self.env.user.id
        self.requester_sign_date = self.datesign

    def button_direct_manager_approve(self):
        self.activity_id.unlink()
        if self.env.user.has_group("purchase_request.group_factory_manager"):
            vals = {
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', u'To Do')],
                    limit=1).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search(
                    [('model', '=', 'purchase.request')], limit=1).id,

                'summary': u'This request is delivered',
            }
            activity_id = self.env['mail.activity'].sudo().create(vals)
        self.write({"state": "direct_manager"})
        self.dir_mgn_sign = self.env.user.id
        self.dir_mgn_sign_date = self.datesign

    def button_factory_manager_approve(self):
        self.activity_id.unlink()
        if self.env.user.has_group("purchase_request.group_general_manager"):
            vals = {
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', u'To Do')],
                    limit=1).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search(
                    [('model', '=', 'purchase.request')], limit=1).id,

                'summary': u'Please approve this request',
            }
            activity_id = self.env['mail.activity'].sudo().create(vals)
        self.write({"state": "factory_manager"})
        self.factory_sign = self.env.user
        self.factory_sign_date = self.datesign

    def button_gm_approve(self):
        self.write({
            "state": "done",
            "gm_sign": self.env.user,
            'gm_sign_sign_date': self.datesign,
        })


    def button_rejected(self):
        return self.write({"state": "rejected"})

    # def button_cancel(self):
    #     return self.write({"state": "canceled"})

    def button_set_draft(self):
        return self.write({"state": "draft"})

    @api.depends('requested_by', 'user_id')
    def _check_department_manager(self):
        self.is_department_manager = False
        for rec in self:
            if rec.requested_by.parent_id.user_id.id == rec._uid:
                rec.is_department_manager = True
                print('T', rec.is_department_manager)
            else:
                rec.is_department_manager = False
                print('F', rec.is_department_manager)

    def _prepare_purchase_request(self):
        return {
            'name': 'New',
            'user_id': self.env.uid,
            'date_order': fields.Date.today(),
            'origin': self.name,
            'partner_id': self.vendor_id.id,
            'purchase_request_id': self.id,
            'state': 'draft',
        }

    def create_po(self):
        requisition_obj = self.env['purchase.order']
        requisition_line_obj = self.env['purchase.order.line']
        res = self._prepare_purchase_request()
        request = requisition_obj.create(res)

        for res in self:
            for rec in res.line_ids:
                res.env['purchase.order.line'].create({'order_id': request.id,
                                                       'product_id': rec.product_id.id,
                                                       'name': rec.name,
                                                       'product_qty': rec.product_qty,
                                                       'price_unit': rec.price_unit,
                                                       })
            res.write({'state': 'po_create'})

    @api.model
    def _prepare_purchase_requisition(self):
        return {
            'user_id': self.env.uid,
            'ordering_date': self.date_start,
            'vendor_id': self.vendor_id.id,
            'purchase_request_id': self.id,
            'is_request': True,
            'state': 'draft',
        }

    def create_requisition(self):
        requisition_obj = self.env['purchase.requisition']
        res = self._prepare_purchase_requisition()
        request = requisition_obj.create(res)

        for res in self:
            for rec in res.line_ids:
                res.env['purchase.requisition.line'].create({'requisition_id': request.id,
                                                             'product_id': rec.product_id.id,
                                                             'product_description_variants': rec.name,
                                                             'product_uom_id': rec.product_id.uom_po_id.id,
                                                             'product_qty': rec.product_qty,
                                                             })
            self.write({'state': 'Requisition_create'})


class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"
    _description = "Purchase Request Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Description", required=True, track_visibility="onchange")
    product_id = fields.Many2one(comodel_name="product.product", string="Product", track_visibility="onchange")
    qty_available = fields.Float(related="product_id.qty_available", string="Quantity On Hand")
    product_qty = fields.Float(string="Requested Quantity", track_visibility="onchange",
                               digits="Product Unit of Measure")
    product_uom_id = fields.Many2one(comodel_name="uom.uom", string="UoM", track_visibility="onchange")
    request_id = fields.Many2one(comodel_name="purchase.request", string="Purchase Request", ondelete="cascade",
                                 readonly=True, index=True)
    company_id = fields.Many2one(comodel_name="res.company", related="request_id.company_id", string="Company",
                                 store=True)
    requested_by = fields.Many2one(comodel_name="hr.employee", related="request_id.requested_by", string="Requested by",
                                   store=True)
    # department_id = fields.Many2one( comodel_name="hr.department",  related="request_id.department_id", store=True, string="Department", readonly=True )

    taxes_id = fields.Many2many('account.tax', string='Taxes',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)
    currency_id = fields.Many2one(related='request_id.currency_id', store=True, string='Currency', readonly=True)
    purpose_purpose = fields.Text('Purchase Purpose')
    notes = fields.Text('Notes')

    def unlink(self):
        if self.request_id.state != 'draft':
            raise UserError(
                _("You cannot delete a purchase request Line which is not draft.")
            )
        return super(PurchaseRequestLine, self).unlink()

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.currency_id,
            'product_qty': self.product_qty,
            'product': self.product_id,
            'partner': self.request_id.vendor_id,
        }

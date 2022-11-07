# -*- coding: utf-8 -*-

from odoo import fields, models ,api , _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class CustodyRequest (models.Model):
    _name = 'custody.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custody Request'

    name = fields.Char('Sequence', required=True, index=True, default='New', readonly=True, copy=False,tracking=True)

    requester_id = fields.Many2one("hr.employee", string="Requester" , required=True )

    requester_job_title = fields.Char(string="Requester Job Title" , related="requester_id.job_title")

    employee_id = fields.Many2one("hr.employee", string="Employee Owed" ,required=True)

    employee_id_job_title = fields.Char(string="Employee Owed Job Title" , related="employee_id.job_title")

    requester_department_id = fields.Many2one("hr.department", string="Requester Department" , related="requester_id.department_id")

    presented_department_id = fields.Many2one("hr.department", string="Presented Department" , required=True)

    date = fields.Date(string="Date", default=lambda *a: fields.Date.today())

    state = fields.Selection([
        ('new', 'New'),
        ('waiting_dm_approve',  'Waiting Department Manager Approval'),
        ('waiting_department_approve',  'Waiting Presented Department Approval'),
        ('waiting_picking_validate',  'Waiting Picking Validate'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='new', string='Stage',tracking=True)

    is_presented_department_manager = fields.Boolean(compute="compute_is_presented_department_manager")

    custody_request_ids = fields.One2many('custody.request.line', 'custody_request_id',string="Custody Details")

    custody_details_ids = fields.One2many('custody.details', 'custody_details_id',string="Custody More Details")
  
    picking_id = fields.Many2one('stock.picking')

    delivery_count = fields.Integer(string='Pickings', compute='_compute_picking_ids')

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',domain="[('code','=','outgoing')]")

    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        default=lambda self: self.env.user.company_id
    )

    location_id = fields.Many2one(
        'stock.location', "Source Location",check_company=True)

    destination_location_id = fields.Many2one(
        'stock.location', string="Destination Location", company_dependent=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]" , required=True ,copy=False)

    acvtivity_id = fields.Many2one('mail.activity', string="Activity")


    def compute_is_presented_department_manager(self):
        for record in self:
            record.is_presented_department_manager = False
            if self.env.user_id.id == record.presented_department_id.manager_id.user_id.id:
                record.is_presented_department_manager = True
           


    def _compute_picking_ids(self):
        for rec in self:
            picking_ids = self.env['stock.picking'].search([('custody_dispensing_id', '=', self.id)])
            rec.delivery_count = len(picking_ids)

    def get_stock_picking_treeview(self):
        view = self.env.ref('stock.vpicktree')
        form_view = self.env.ref('stock.view_picking_form')
        return {
            'name': _('Pickings'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('origin', '=', self.name)],
            'views': [(view.id, 'tree'), (form_view.id, 'form')],
        }

    @api.model
    def create(self, vals):
        if vals:
            vals['name'] = self.env['ir.sequence'].next_by_code('custody.request.seq') or _('New')
        return super(CustodyRequest, self).create(vals) 

    def action_submit(self):
        if self.custody_request_ids:
            self.state = 'waiting_dm_approve'
        else:
            raise ValidationError(_('Please Add  at least one line in Custody Details.'))
      
    def action_dm_approve(self):
        self.acvtivity_id.unlink()
        if self.presented_department_id.manager_id.user_id:
            vals = {
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', u'To Do')],
                    limit=1).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search(
                    [('model', '=', 'custody.request')], limit=1).id,
                'user_id':self.presented_department_id.manager_id.user_id.id,
                'summary': u'New custody request',
            }
            # add lines
            acvtivity_id = self.env['mail.activity'].sudo().create(vals)

        self.state = 'waiting_department_approve'
        
    def generate_picking(self):
        if self.custody_details_ids:
            
                # Stock Picking order entry
                picking = self.env['stock.picking'].create({
                    'custody_dispensing_id': self.id,
                    'state': 'draft',
                    'origin': self.name,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.destination_location_id.id,
                    'picking_type_id': self.picking_type_id.id,
                })
                for line in self.custody_request_ids:
                    StockMove = self.env['stock.move'].create({
                        'product_id': line.product_id.id,
                        'state': 'draft',
                        'product_uom_qty': 1,
                        'location_id':self.location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                        'name': line.product_id.name,
                        'product_uom': line.product_id.uom_id.id,
                        'company_id': self.company_id.id,
                        'picking_id': picking.id,
                        'move_line_ids': [(0, 0, {
                            'product_id': line.product_id.id,
                            'product_uom_id':  line.product_id.uom_id.id,
                            'location_id': self.location_id.id,
                            'location_dest_id': self.destination_location_id.id,
                            'picking_id': picking.id,
                        })],
                    })
                    StockMove._action_assign()
                picking.action_assign()
                self.picking_id = picking
                self.state = "waiting_picking_validate"
        else:
            raise ValidationError(_('Please Add at least one line in More Details.'))

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    # Notify the department requesting that delivery is done
    def send_notification_delivery_done(self):
        self.acvtivity_id.unlink()
        if self.requester_department_id.manager_id.user_id:
            vals = {
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', u'To Do')],
                    limit=1).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search(
                    [('model', '=', 'custody.request')], limit=1).id,
                'user_id':self.requester_department_id.manager_id.user_id.id,
                'summary': u'This custody is deliverd',
            }
            # add lines
            acvtivity_id = self.env['mail.activity'].sudo().create(vals)
   
    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        self.location_id = self.picking_type_id.default_location_src_id.id

class CustodyRequestLine(models.Model):
    _name = 'custody.request.line'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Name', required=True)

    type = fields.Selection([
        ('refunded', 'Refunded'),
        ('non_refunded', 'Non Refunded'),
    ], string='Type',)

    available_qty = fields.Float(string='QTY Available' , compute='_compute_onhand')

    requster_note = fields.Text(string="Notes")

    custody_request_id = fields.Many2one('custody.request')

    custody_return_id  = fields.Many2one('custody.return')

    @api.depends('custody_request_id.location_id')
    def _compute_onhand(self):
        for rec in self:
            p = n = q = 0
            locations = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id),
                                                        ('location_id', '=',
                                                         rec.custody_request_id.location_id.id)])
            if locations:
                for z in locations:
                    q += z.quantity

                rec.available_qty = q
            else:
                rec.available_qty = 0


class CustodyRequestDetails(models.Model):
    _name = 'custody.details'

    custody_id = fields.Many2one('custody.request.line', string='Custody', required=True)

    brand= fields.Char(string="Brand")

    number = fields.Char(string="Number")

    custody_details_id = fields.Many2one('custody.request')

    presented_department_note = fields.Text(string="Presented Department Notes")

class StockPicking(models.Model):
    _inherit = "stock.picking"

    custody_dispensing_id = fields.Many2one('custody.request', 'Custody Ref', readonly=True)
    
    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        if self.custody_dispensing_id:
            self.custody_dispensing_id.action_done()
            self.custody_dispensing_id.send_notification_delivery_done()
        return res
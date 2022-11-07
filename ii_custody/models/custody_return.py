# -*- coding: utf-8 -*-

from odoo import fields, models ,api , _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class CustodyReturn(models.Model):
    _name = 'custody.return'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custody Request'

    name = fields.Char('Sequence', required=True, index=True, default='New', readonly=True, copy=False,tracking=True)

    requester_id = fields.Many2one("hr.employee", string="Employee" , required=True ,related='custody_request_id.employee_id')

    requester_job_title = fields.Char(string="Requester Job Title" , related="requester_id.job_title")

    requester_department_id = fields.Many2one("hr.department", string="Requester Department" , related="requester_id.department_id")

    returned_to_department_id = fields.Many2one("hr.department", string="Returned To Department" , related="custody_request_id.presented_department_id" , required=True)

    date = fields.Date(string="Date", default=lambda *a: fields.Date.today())

    type = fields.Selection([
        ('clearance_req', 'Clearance Request'),
        ('service_ter',  'Service Termination'),
       
    ], string='Clearance Type',required=True)


    state = fields.Selection([
        ('new', 'New'),
        ('waiting_dm_approve',  'Waiting Department Manager Approval'),
        ('waiting_department_approve',  'Waiting Presented Department Approval'),
        ('waiting_picking_validate',  'Waiting Picking Validate'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='new', string='Stage',tracking=True)

    custody_request_ids = fields.One2many('custody.request.line', 'custody_return_id',string="Custody  Clear Details")
  
    picking_id = fields.Many2one('stock.picking')

    delivery_count = fields.Integer(string='Pickings', compute='_compute_picking_ids')

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',domain="[('code','=','incoming')]")

    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        default=lambda self: self.env.user.company_id
    )

    location_id = fields.Many2one(
        'stock.location', string="Source Location", company_dependent=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]" , required=True ,copy=False)
   

    destination_location_id = fields.Many2one(
        'stock.location', string="Destination Location", company_dependent=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]" , required=True ,copy=False)

    custody_request_id = fields.Many2one("custody.request", string="Request No.",required=True)

    acvtivity_id = fields.Many2one('mail.activity', string="Activity")

    def _compute_picking_ids(self):
        for rec in self:
            picking_ids = self.env['stock.picking'].search([('custody_clear_id', '=', self.id)])
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
            vals['name'] = self.env['ir.sequence'].next_by_code('custody.return.seq') or _('New')
        return super(CustodyReturn, self).create(vals) 

    def action_submit(self):
        if self.custody_request_ids:
            self.state = 'waiting_dm_approve'
        else:
            raise ValidationError(_('Please add at least one line in Custody Details.'))
      
    def action_dm_approve(self):
        self.acvtivity_id.unlink()
        if self.returned_to_department_id.manager_id.user_id:
            vals = {
                'activity_type_id': self.env['mail.activity.type'].sudo().search(
                    [('name', 'like', u'To Do')],
                    limit=1).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].sudo().search(
                    [('model', '=', 'custody.return')], limit=1).id,
                'user_id':self.returned_to_department_id.manager_id.user_id.id,
                'summary': u'New custody clearance',
            }
            # add lines
            acvtivity_id = self.env['mail.activity'].sudo().create(vals)

        self.state = 'waiting_department_approve'
        
    def generate_picking(self):
            
        # Stock Picking order entry
        picking = self.env['stock.picking'].create({
            'custody_clear_id': self.id,
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


    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        self.destination_location_id = self.picking_type_id.default_location_dest_id.id

    @api.onchange('custody_request_id')
    def onchange_custody_request_id(self):
        self.custody_request_ids = self.custody_request_id.custody_request_ids.ids

class StockPicking(models.Model):
    _inherit = "stock.picking"

    custody_clear_id = fields.Many2one('custody.return', 'Custody Ref', readonly=True)
   
# -*- coding: utf-8 -*-

from odoo import fields, models ,api , _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class CustodyExchange (models.Model):
    _name = 'custody.exchange'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custody Exchange'

    name = fields.Char('Sequence', required=True, index=True, default='New', readonly=True, copy=False,tracking=True)

    requester_id = fields.Many2one("hr.employee", string="Requester" , required=True )

    requester_job_title = fields.Char(string="Requester Job Title" , related="requester_id.job_title")

    employee_id = fields.Many2one("hr.employee", string="Employee Owed")

    employee_id_job_title = fields.Char(string="Employee Owed Job Title" , related="employee_id.job_title")

    requester_department_id = fields.Many2one("hr.department", string="Requester Department" , related="requester_id.department_id")

    presented_department_id = fields.Many2one("hr.department", string="Presented Department" , required=True)

    date = fields.Date(string="Date", default=lambda *a: fields.Date.today())

    custody_request_id = fields.Many2one("custody.request", string="Request No.",required=True)

    state = fields.Selection([
        ('new', 'New'),
        ('waiting_dm_approve',  'Waiting Department Manager Approval'),
        ('waiting_department_approve',  'Waiting Presented Department Approval'),
        ('waiting_picking_validate',  'Waiting Picking Validate'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='new', string='Stage',tracking=True)

    custody_exchange_ids = fields.One2many('custody.exchange.line', 'custody_exchange_id',string="Exchange Custody Details")

    picking_id = fields.Many2one('stock.picking')

    delivery_count = fields.Integer(string='Pickings', compute='_compute_picking_ids')

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',domain="[('code','=','outgoing')]")

    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company', 
        default=lambda self: self.env.user.company_id
    )

    location_id = fields.Many2one(
        'stock.location', "Source Location",check_company=True, required=True,)
   
    destination_location_id = fields.Many2one(
        'stock.location', string="Destination Location", company_dependent=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', allowed_company_ids[0])]" , required=True ,copy=False)

    acvtivity_id = fields.Many2one('mail.activity', string="Activity")

    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost',store=True)

    requested = fields.Boolean('Requested', default=False ,copy=False)

    @api.depends('custody_exchange_ids')
    def _compute_total_cost(self):
         for rec in self:
            total_cost = 0.0
            rec.total_cost = 0
            for line in rec.custody_exchange_ids:
                total_cost += line.cost
            rec.total_cost = total_cost

    @api.depends('custody_exchange_ids.cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = 0.0
            for line in rec.custody_exchange_ids:
                rec.total_cost += line.cost

    def _compute_picking_ids(self):
        for rec in self:
            picking_ids = self.env['stock.picking'].search([('custody_ex_dispensing_id', '=', self.id)])
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
            vals['name'] = self.env['ir.sequence'].next_by_code('custody.exchange.seq') or _('New')
        return super(CustodyExchange, self).create(vals) 

    def action_submit(self):
        if self.custody_exchange_ids:
            self.state = 'waiting_dm_approve'
        else:
            raise ValidationError(_('Please Add  at least one line in Exchange Custody Details.'))
      
    def action_dm_approve(self):
        self.acvtivity_id.unlink()
        if self.requested : 
            if self.presented_department_id.manager_id.user_id:
                vals = {
                    'activity_type_id': self.env['mail.activity.type'].sudo().search(
                        [('name', 'like', u'To Do')],
                        limit=1).id,
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', '=', 'custody.exchange')], limit=1).id,
                    'user_id':self.presented_department_id.manager_id.user_id.id,
                    'summary': u'New custody exchange',
                }
                # add lines
                acvtivity_id = self.env['mail.activity'].sudo().create(vals)

            self.state = 'waiting_department_approve'
        else:
            raise ValidationError(_('Please generate loan request first.'))
        
    def generate_picking(self):
        # Stock Picking order entry
        picking = self.env['stock.picking'].create({
            'custody_ex_dispensing_id': self.id,
            'state': 'draft',
            'origin': self.name,
            'location_id': self.location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'picking_type_id': self.picking_type_id.id,
        })
        for line in self.custody_exchange_ids:
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
                    'location_id':self.location_id.id,
                    'location_dest_id': self.destination_location_id.id,
                    'picking_id': picking.id,
                })],
            })
            StockMove._action_assign()
        picking.action_assign()
        self.picking_id = picking
        self.state = "waiting_picking_validate"

    def generate_loan_req(self):
        view_id = self.env.ref('hr_loan.view_hr_loan_form').id
        for rec in self:
            return {
                'name': "Loan Requests",
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'hr.loan',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': {
                    'default_employee_id': rec.employee_id.id,
                    'default_loan_amount':rec.total_cost,
                    'default_state': 'draft',
                    'default_custody_exchange_id': rec.id,
                }
            }

    def action_view_loan_req(self):
        action = self.env.ref('hr_loan.action_hr_loan_request').read([])[0]
        action['domain'] = [('custody_exchange_id', '=', self.id)]
        return action
     

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
                    [('model', '=', 'custody.exchange')], limit=1).id,
                'user_id':self.requester_department_id.manager_id.user_id.id,
                'summary': u'This custody is deliverd',
            }
            # add lines
            acvtivity_id = self.env['mail.activity'].sudo().create(vals)

    @api.onchange('picking_type_id')
    def onchange_picking_type_id(self):
        self.location_id = self.picking_type_id.default_location_src_id.id

    @api.constrains('custody_exchange_ids')
    def _check_custody(self):
        for rec in self:
            product = []
            for record in self.custody_request_id.custody_request_ids:
                product.append(record.product_id.id)
            for record in rec.custody_exchange_ids:
                if record.product_id.id not in product:
                     raise ValidationError(_('Please choose custody that in request'))


class CustodyExchangeLine(models.Model):
    _name = 'custody.exchange.line'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Name', required=True)

    type = fields.Selection([
        ('refunded', 'Refunded'),
        ('non_refunded', 'Non Refunded'),
    ], string='Type', required=True)

    requster_note = fields.Text(string="Notes")

    custody_exchange_id = fields.Many2one('custody.exchange')

    requested = fields.Boolean('Requested', default=False ,copy=False)

    exchange_reason = fields.Selection([
        ('damage', 'Damage'),
        ('loss',  'Loss'),
    ], string='Exchange Reason',)

    cost = fields.Float(string='Cost',required=True)

    available_qty = fields.Float(string='QTY Available' , compute='_compute_onhand')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.cost = self.product_id.standard_price

    def generate_scrap(self):
        view_id = self.env.ref('stock.stock_scrap_form_view').id
        for rec in self:
            return {
                'name': "Scrap Order",
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.scrap',
                'view_id': view_id,
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': {
                    'default_product_id': rec.product_id.id,
                    'default_custody_exchange_line_id': rec.id,
                    'default_state': 'draft',
                    'default_origin': rec.custody_exchange_id.name,
                }
            }

    def action_view_scrap(self):
        action = self.env.ref('stock.action_stock_scrap').read([])[0]
        action['domain'] = [('custody_exchange_line_id', '=', self.id)]
        return action
    
    @api.depends('custody_exchange_id.location_id')
    def _compute_onhand(self):
        for rec in self:
            p = n = q = 0
            locations = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id),
                                                        ('location_id', '=',
                                                         rec.custody_exchange_id.location_id.id)])
            if locations:
                for z in locations:
                    q += z.quantity

                rec.available_qty = q
            else:
                rec.available_qty = 0


class StockPicking(models.Model):
    _inherit = "stock.picking"

    custody_ex_dispensing_id = fields.Many2one('custody.exchange', 'Custody Ref', readonly=True)
    
    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        if self.custody_ex_dispensing_id:
            self.custody_ex_dispensing_id.action_done()
            self.custody_ex_dispensing_id.send_notification_delivery_done()
        return res

class StockScrap(models.Model):
    _inherit = "stock.scrap"

    custody_exchange_line_id = fields.Many2one('custody.exchange.line', 'Custody Exchange Line Ref', readonly=True)
    
    @api.constrains('custody_exchange_line_id')
    def _check_custody(self):
        for rec in self:
            if rec.custody_exchange_line_id:
                rec.custody_exchange_line_id.requested = True

class LoanRequest(models.Model):
    _inherit = "hr.loan"

    custody_exchange_id = fields.Many2one('custody.exchange', 'Custody Exchange Ref', readonly=True)
    
    @api.constrains('custody_exchange_id')
    def _check_custody(self):
        for rec in self:
            if rec.custody_exchange_id:
                rec.custody_exchange_id.requested = True

    @api.onchange('loan_type')
    def onchange_loan_type(self):
        """
        A method to change loan configuration when loan type was change.
        """
        self._get_max_loan()
        self.treasury_account_id = self.loan_type.treasury_account_id.id
        self.emp_account_id = self.loan_type.emp_account_id.id
        self.journal_id = self.loan_type.journal_id.id
        self.no_month = self.loan_type.no_month
        emp_salary = self.emp_salary
        if not self.custody_exchange_id:
            self.loan_amount = self.loan_type.amount
        if self.loan_type.installment_type == 'depends_on_payroll':
            self.loan_amount = (emp_salary * self.loan_type.percentage) / 100

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
import math
import babel
import time
from odoo import tools

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('dep_manger', 'Department Manager'),('approve','Approved')])

    check_discount = fields.Boolean(compute ='compute_check_discount')
    # activity_id = fields.Many2one('mail.activity', string='Activity')

    @api.depends('order_line', 'partner_id')
    def compute_check_discount(self):
        self.check_discount = False
        for rec in self.order_line:
            if rec.discount > 0:
                self.check_discount = True


    def action_dep_manger(self):
        for rec in self:
            users = self.env['res.groups'].sudo().search([
                ('id', '=',self.env.ref('zaway_sale_custom.group_sale_department_manager').id)]).users
            for user in users:
                vals = {
                    'activity_type_id': self.env['mail.activity.type'].sudo().search(
                        [('name', 'like', 'To Do')],limit=1).id,

                    'res_id': rec.id,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'sale.order')],
                                                                       limit=1).id,
                    'user_id': user.id,
                    'summary': 'You need to Approva Discount For ' + rec.name,
                        }
            self.activity_ids = self.env['mail.activity'].sudo().create(vals)

            rec.state = 'dep_manger'

    def action_dep_manger_approve(self):
        for rec in self:
            rec.state = 'approve'


    def customer_timer_notification(self):
        customer = self.env['res.partner'].search([])
        for cus in customer:
            for rec in self.env['sale.order'].search([('partner_id','=',cus.id)],order='date_order asc',limit=1):
                diff = fields.Date.today() - rec.date_order.date()
                if diff.days > rec.company_id.compute_day:
                    users = self.env['res.groups'].search([('id', '=',self.env.ref('sales_team.group_sale_manager').id)],limit=1).users
                    for user in users:
                        print("::::::::::::::::::;;;",user)
                        vals = {
                        'activity_type_id': self.env['mail.activity.type'].sudo().search(
                            [('name', '=', u'To Do')],
                            limit=1).id,
                        'res_id': cus.id,
                        'res_model_id': self.env['ir.model'].sudo().search(
                            [('model', '=', 'res.partner')], limit=1).id,
                        'user_id': user.id,
                        'summary': 'The EX-Form is about to Customer Expiration',
                    }
                    acvtivity_id = self.env['mail.activity'].sudo().create(vals)
                    print("***********************",acvtivity_id)













                        # body = ('<strong>Customer Expiration<br/> Dear : %s<br/> contract<br/></strong>') % (cus.name)
                        # message =self.env['mail.message']
                        # vals={    
                        #     'message_type': 'notification',
                        #     'author_id' : self.env.user.id,
                        #     'body': body,
                        #     'model': 'sale.order',
                        #     'res_id' :rec.id,
                        #     'partner_ids':[(6, 0, [user.partner_id.id])] 
                        #     }
                        # message_id = message.create(vals)
                        # notification_id = self.env['mail.notification'].create({
                        #     'mail_message_id' : message_id.id, 
                        #     'notification_type' :'inbox',
                        #     'res_partner_id' : user.partner_id.id or self.env.user.partner_id.id})



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_unit_usd = fields.Char('Unit Price USD',compute='compute_price_unit_usd')
    @api.onchange('price_unit')
    def compute_price_unit_usd(self):
        for rec in self:
            if rec.price_unit:
                currency_usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                rates = self.env['res.currency.rate'].search([('currency_id', '=',currency_usd.id)],order='name desc', limit=1)
                for currency in rates:
                    rec.price_unit_usd = currency.currency_id.symbol + ' '+ str(rec.price_unit / currency.inverse_company_rate)

# class ProductPricelist(models.Model):
#     _inherit = 'product.pricelist'

#     use_two_currency = fields.Boolean(string="Use Two Currency?")
#     currency_id_usd = fields.Many2one('res.currency',string="Second Currency")

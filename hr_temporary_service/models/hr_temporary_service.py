# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrTemporaryService(models.Model):
    _name = 'hr.temporary.service'
    _rec_name = 'reference'
    _inherit = 'mail.thread', 'mail.activity.mixin', 'portal.mixin'
    name = fields.Char(string='Name')
    reference = fields.Char(string='ref')
    note = fields.Text(string='Note')
    date = fields.Date(string="Date", required=False, default=fields.Date.context_today)
    partner_ids = fields.Many2many('res.partner', string='partners')
    line_ids = fields.One2many("temporary.service.line", "service_id", string="Partners", required=False, )
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('approved', 'Approved'),('cancel', 'Cancel')], default='draft',
                             tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    analytic_account_id = fields.Many2one('account.analytic.account', 'analytic account',
                                          readonly=False)
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount')
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True, )
    pay_type = fields.Selection(string="Pay Type", selection=[('hours', 'Hours'),
                                                              ('days', 'Days'),
                                                              ], required=True,default='days')
    wage_hour = fields.Float(string="Wage Hours")
    wage_day = fields.Float(string="Wage Days")
    move_id = fields.Many2one("account.move", string="Move", required=False, readonly=True)

    def set_to_draft(self):
        self.write({'state': 'draft'})

    @api.constrains('line_ids')
    def _check_number_of_days(self):
        duration = (self.date_to - self.date_from).days + 1 
        for lin in self.line_ids:
            if lin.no_days > duration:
                raise ValidationError(
                    _("Number of days is grater than duration between date from and date to !"))

    @api.constrains('date_from', 'date_to', 'line_ids')
    def _check_employee_temp_service(self):
        """A method to check the create of another temporary service for same labor """
        for line in self.line_ids:
            pay_service = self.env['hr.temporary.service'].search([
                ('line_ids.labor_id', '=', line.labor_id.id),
                ('id', '!=', self.id)
            ])
            for rec in pay_service:
                if (rec.date_from == self.date_from and rec.date_to == self.date_to) or (
                        self.date_from >= rec.date_from and self.date_from <= rec.date_to) or (
                        self.date_to >= rec.date_from and self.date_to <= rec.date_to) or (
                        self.date_from >= rec.date_from and self.date_from <= rec.date_to and self.date_to >= rec.date_from and self.date_to <= rec.date_to):
                    raise ValidationError(
                        _("You can not  create two temporary service  the same period for same labor!"))

    def action_compute_wage(self):
        for rec in self:
            if rec.pay_type == 'days':
                for line in rec.line_ids:
                    line.wage = (line.no_days * rec.wage_day) + line.extra_pay
            if rec.pay_type == 'hours':
                for line in rec.line_ids:
                    line.wage = (line.no_hours * rec.wage_hour) + line.extra_pay

    @api.depends('pay_type', 'line_ids.wage')
    def _compute_total_amount(self):
        """
        A method to compute service total amount
        """
        total = 0.0
        for line in self.line_ids:
            total += line.wage
        self.total_amount = total

    def confirmed(self):
        """
        A method to confirm service
        """
        self.write({'state': 'confirmed'})

    def create_invoice(self):
        """
        A method to create invoice
        """
        if not self.company_id.labor_account_id:
            raise ValidationError(_("Please Configure Account For Temporary Service."))
        domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company_id.id),
        ]
        journal_id = self.env['account.journal'].search(domain, limit=1)
        lines = []
        if self.company_id.detailed_payment:
            for rec in self.line_ids:
                lines.append((0, 0, {
                    'name': rec.labor_id.name,
                    'account_id': self.company_id.labor_account_id.id,
                    'analytic_account_id': self.analytic_account_id.id,
                    'quantity': 1,
                    'price_unit': rec.wage,
                }))
        else:
            lines.append((0, 0, {
                'name': self.name,
                'account_id': self.company_id.labor_account_id.id,
                'analytic_account_id': self.analytic_account_id.id,
                'quantity': 1,
                'price_unit': self.total_amount,
            }))
        move_id = self.env['account.move'].sudo().create({
            'move_type': 'in_receipt',
            'hr_receipt': True,
            'journal_id': journal_id.id,
            'invoice_line_ids': lines,
        })
        self.move_id = move_id
        self.write({'state': 'approved'})

    @api.model
    def create(self, vals):
        """
        A method to create sequence
        """
        seq = self.env['ir.sequence'].next_by_code('labor.sequence') or 'NEW'
        vals['reference'] = seq
        return super(HrTemporaryService, self).create(vals)

    def action_cancel(self):
        """
        A method to cancel incentive
        """
        for rec in self:
            if rec.move_id:
                if rec.move_id.state == 'draft':
                    rec.state = 'cancel'
                    rec.move_id.button_cancel()
                elif rec.move_id.state == 'posted':
                    raise ValidationError(_("There is a Receipt linked with this record must be canceled first in order to cancel the record."))
                elif rec.move_id.state == 'cancel':
                    rec.state = 'cancel'
                else:
                    raise ValidationError(
                        _("You should Cancel Or Delete The Receipt linked to this record first!"))
            else:
                rec.state = 'cancel'

class TemporaryServiceLine(models.Model):
    _name = 'temporary.service.line'

    labor_id = fields.Many2one("res.partner", string="Name", required=False, )
    wage = fields.Float(string="Wage", required=False, )
    no_days = fields.Integer(string="Number Of Days", required=False, )
    no_hours = fields.Integer(string="Number Of Hours", required=False, )
    service_id = fields.Many2one("hr.temporary.service", string="Service", required=False, )
    extra_pay = fields.Float(string="Extra Pay", required=False, )

class ResPartnerService(models.Model):
    _inherit = 'res.partner'

    service_partner = fields.One2many('temporary.service.line', 'labor_id', string="Temporory Service Labor")

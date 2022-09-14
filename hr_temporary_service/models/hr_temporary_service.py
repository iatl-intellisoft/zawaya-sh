# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from re import T
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import datetime


class HrTemporaryService(models.Model):
    _name = 'hr.temporary.service'
    _rec_name = 'reference'

    name = fields.Char(string='Name')
    reference = fields.Char(string='ref')
    note = fields.Text(string='Note')
    date = fields.Date(string="Date", required=False, default=fields.Date.context_today)
    partner_ids = fields.Many2many('res.partner', string='partners')
    line_ids = fields.One2many("temporary.service.line", "service_id", string="Partners", required=False, )
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed_sup_labor', 'supervisor Labor'), ('approved_hr_adm', 'HR admin Approve'),
         ('approved_finance', ' Finance Approve'), ('refuse', 'Refuse'), ('cancel', 'Cancel')],
        default='draft',
        tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    # analytic_account_id = fields.Many2one('account.analytic.account', 'analytic account',
    #                                       related='company_id.analytic_account_id', readonly=False)
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount')
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True, )
    pay_type = fields.Selection(string="Pay Type", selection=[('hours', 'Hours'),
                                                              ('days', 'Days'),
                                                              ], required=True, default='days')
    wage_hour = fields.Float(string="Wage Hours")
    wage_day = fields.Float(string="Wage Days")
    move_id = fields.Many2one("account.move", string="Move", required=False, readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    temporary_ser_debit_account_id = fields.Many2one('account.account', string='Dedit Account',
                                                     related='company_id.temporary_ser_debit_account_id',
                                                     readonly=False)
    temporary_ser_credit_account_id = fields.Many2one('account.account', string='Credit Account',
                                                      related='company_id.temporary_ser_credit_account_id')
    temporary_service_journal_id = fields.Many2one('account.journal', string='Journal',
                                                   related='company_id.temporary_service_journal_id')
    tem_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                              related='company_id.tem_account_analytic_id', readonly=False)

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
                ('line_ids.labor', '=', line.labor.id),
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
        self.write({'state': 'confirmed_sup_labor'})

    def approved_hr_adm(self):
        """
        A method to confirm service
        """
        self.write({'state': 'approved_hr_adm'})

    def approved_finance(self):
        """
        A method to confirm service
        """
        self.write({'state': 'approved_finance'})

    # def create_invoice(self):
    #     """
    #     A method to create invoice
    #     """
    #     if not self.company_id.labor_account_id:
    #         raise ValidationError(_("Please Configure Account For Temporary Service."))
    #     domain = [
    #         ('type', '=', 'purchase'),
    #         ('company_id', '=', self.company_id.id),
    #     ]
    #     journal_id = self.env['account.journal'].search(domain, limit=1)
    #     lines = []
    #     if self.company_id.detailed_payment:
    #         vals = []
    #         for line in self.line_ids:
    #             if not line.department_id.analytic_account_id:
    #                 raise ValidationError(
    #                     _('Please Add Analytic Account in %s', line.department_id.name + ' Department'))
    #             else:
    #                 vals.append(
    #                     [line.department_id.id, line.department_id.name, line.department_id.analytic_account_id.id,
    #                      line.wage])
    #         lines = self.create_lines_with_analytic(vals)
    #
    #     else:
    #         lines.append((0, 0, {
    #             'name': self.name,
    #             'account_id': self.company_id.labor_account_id.id,
    #             'analytic_account_id' : self.env.company.tem_account_analytic_id.id if self.env.company.tem_account_analytic_id.id else False,
    #             'quantity': 1,
    #             'price_unit': self.total_amount,
    #         }))
    #     move_id = self.env['account.move'].sudo().create({
    #         'move_type': 'in_receipt',
    #         'hr_receipt': True,
    #         'journal_id': journal_id.id,
    #         'currency_id': self.currency_id.id,
    #         'invoice_line_ids': lines,
    #         'analytic_account_id' : self.env.company.tem_account_analytic_id.id if self.env.company.tem_account_analytic_id.id else False,
    #     })
    #     self.move_id = move_id
    #     self.write({'state': 'approved'})

    def create_lines_with_analytic(self, vals):
        lines = []
        departments = self.line_ids.mapped('department_id').ids
        line_dict = dict()
        for dept in departments:
            if dept in line_dict:
                pass
            else:
                line_dict[dept] = []

        for line in self.line_ids:
            for key in line_dict:
                if line.department_id.id == key:
                    line_dict[key].append(line)

        for key in line_dict:
            wage = 0.0
            name = ''
            analytic = False
            for val in line_dict[key]:
                wage += val.wage
                name = val.department_id.name
                analytic = val.department_id.analytic_account_id.id
            lines.append((0, 0, {
                'name': name,
                'account_id': self.company_id.labor_account_id.id,
                'analytic_account_id': analytic,
                'quantity': 1,
                'price_unit': wage,
            }))
        return lines

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
                    raise ValidationError(_(
                        "There is a Receipt linked with this record must be canceled first in order to cancel the record."))
                elif rec.move_id.state == 'cancel':
                    rec.state = 'cancel'
                else:
                    raise ValidationError(
                        _("You should Cancel Or Delete The Receipt linked to this record first!"))
            else:
                rec.state = 'cancel'

    def create_account_move(self):
        move_obj = self.env['account.move']
        for rec in self:
            # temporary_service_journal_id
            # tem_account_analytic_id
            # temporary_service_journal_id
            if rec.temporary_ser_debit_account_id and rec.temporary_ser_credit_account_id and rec.temporary_service_journal_id:
                lines = []
                move_id = move_obj.create({
                    'temporary_service_id': rec.id,
                    'date': fields.date.today(),
                    'ref': rec.reference,
                    'currency_id': rec.currency_id.id,
                    'move_type': 'entry',
                    'journal_id': rec.temporary_service_journal_id.id,
                    # 'hr_receipt': True,
                    'line_ids': [(0, 0, {
                        'currency_id': rec.currency_id.id,
                        'partner_id': rec.line_ids.labor.id,
                        'account_id': rec.temporary_ser_debit_account_id.id,
                        'debit': abs(rec.total_amount),
                        'credit': 0,
                        'analytic_account_id': rec.tem_account_analytic_id.id,
                        'tem_service_line_id': rec.id,
                    }), (0, 0, {
                        'currency_id': rec.currency_id.id,
                        'partner_id': rec.line_ids.labor.id,
                        'account_id': rec.temporary_ser_credit_account_id.id,
                        'debit': 0,
                        'credit': abs(rec.total_amount),
                        'analytic_account_id': rec.tem_account_analytic_id.id,
                        'tem_service_line_id': rec.id,
                    })],

                })

                rec.move_id = move_id
                self.write({'state': 'approved_finance'})
            else:
                raise ValidationError(_("Please configure temporary service's account and journal in settings"))


class TemporaryServiceLine(models.Model):
    _name = 'temporary.service.line'

    labor = fields.Many2one("hr.labor", string="Name", required=False, )
    function = fields.Many2one(string="Job position", related="labor.job_id")
    department_id = fields.Many2one('hr.department', related="labor.department_id")
    wage = fields.Float(string="Wage", required=False, )
    no_days = fields.Float(string="Number Of Days", required=False, )
    no_hours = fields.Float(string="Number Of Hours", required=False, )
    service_id = fields.Many2one("hr.temporary.service", string="Service", required=False, )
    extra_pay = fields.Float(string="Extra Pay", required=False, )



class HrLabor(models.Model):
    _name = 'hr.labor'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    phone = fields.Char(string="Phone")
    address = fields.Char(string="Address")
    job_id = fields.Many2one('hr.job', string="Job Position")
    department_id = fields.Many2one("hr.department")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments", required=True)
    start_date_work = fields.Datetime(string="Start Date")
    end_date_work = fields.Datetime(string="End Date")
    start_date_health = fields.Date(string="Start Date")
    end_date_health = fields.Date(string="End Date")
    active = fields.Boolean(string="Active", default=True)

    def send_notification_in_chatter(self):
        return True
        # res = self.env['hr.labor'].search([])
        # for rec in res:

        #     call_time = str(fields.Datetime.now().month - rec.start_date_work.month)
        #     notification_ids = []
        #     if int(call_time) == 3 or int(call_time) >= 3:
        #         # job_controller_group = rec.env['res.groups'].search([('name', '=', 'Job Controller')])

        #         # for line in job_controller_user:
        #         notification_ids.append((0, 0, {
        #             'res_partner_id': rec.department_id.manager_id.id,
        #             'notification_type': 'inbox'}))
        #         rec.message_post(body=_('%s is been done for 3 months') % rec.name,
        #                          message_type='notification',
        #                          subtype_xmlid='mail.mt_comment', author_id=rec.env.user.partner_id.id,
        #                          notification_ids=notification_ids)

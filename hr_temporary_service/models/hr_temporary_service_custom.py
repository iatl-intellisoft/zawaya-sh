# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HrTemporaryServiceAttendance(models.Model):
    _name = "hr.temporary.service.attendance"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'name'
    name = fields.Char(string="", required=False, default='NEW')
    date = fields.Date(string="Date", required=True, default=datetime.today())
    # location = fields.Selection(string="Location", selection=[('axxa', 'Axxa'), ('elbagir', 'Elbagir'), ],
    #                             required=True, )
    attendance_ids = fields.One2many(comodel_name="hr.temporary.service.attendance.line", inverse_name="service_id",
                                     string="", required=False, )
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('cancel', 'Cancel')
                              ], string="State", default='draft', tracking=5, copy=False, )

    def confirm(self):
        self.state = 'confirmed'

    def reset(self):
        self.state = 'draft'

    def cancel(self):
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        """
        A method to create sequence
        """
        sequences = self.env['ir.sequence'].sudo().search([('code', '=', 'attendance.sequence')])
        # if vals['location'] == 'axxa':
        #     prefix = 'AXXA/ATTEND/%(year)s/%(month)s/'
        #     for seq in sequences:
        #         seq.write({'prefix': prefix})
        # else:
        #     prefix = 'ELBAG/TEP-Service/%(year)s/%(month)s/'
        #     for seq in sequences:
        #         seq.write({'prefix': prefix})
        vals['name'] = self.env['ir.sequence'].next_by_code('attendance.sequence') or ('NEW')
        return super(HrTemporaryServiceAttendance, self).create(vals)


class HrTemporaryServiceAttendanceLine(models.Model):
    _name = "hr.temporary.service.attendance.line"

    service_id = fields.Many2one(comodel_name="hr.temporary.service.attendance", string="", required=False, )
    labor_id = fields.Many2one("res.partner", string="Name", required=False,
                               domain="[('labor','=',True)]")
    # location = fields.Selection(string="Location", selection=[('axxa', 'Axxa'), ('elbagir', 'Elbagir'), ],
    #                             related='service_id.location', )
    extra_pay = fields.Float(string="Extra Pay", required=False, )
    extra_hour = fields.Float("Extra Hours")
    extra_hour_holiday = fields.Float("Extra Holiday Hours")
    note = fields.Text(string="Note", required=False, )
    date = fields.Date(string="Date", required=False, related='service_id.date')


class LaborJobType(models.Model):
    _name = 'labor.job.type'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string="Name", required=False, )
    day_rate = fields.Float(string="Day Rate", required=False, )


class ResPartner(models.Model):
    _inherit = 'res.partner'
    # job_type_id = fields.Many2one(comodel_name="labor.job.type", string="Job", required=False, )
    # location = fields.Selection(string="Location", selection=[('axxa', 'Axxa'), ('elbagir', 'Elbagir'), ],
    #                             required=True, )


class HrTemporaryService(models.Model):
    _inherit = 'hr.temporary.service'

    working_hours = fields.Float(string='Working Hours:')
    work_day = fields.Integer("Work Days", compute='_compute_work_days')
    payment_done = fields.Boolean('Done')
    payment_count = fields.Integer('Done', compute='_get_payment_count')
    tempserv_id = fields.One2many('finance.approval', 'finapprov_id')
    # location = fields.Selection(string="Location", selection=[('axxa', 'Axxa'), ('elbagir', 'Elbagir'), ],
    #                             required=True, )
    reference = fields.Char(string='ref', default='NEW')

    def get_labors(self):
        for rec in self:
            res = []
            rec.line_ids.unlink()
            labors = rec.env['res.partner'].search([('labor', '=', True)])
            for labor in labors:
                attends = rec.env['hr.temporary.service.attendance.line'].search(
                    [('service_id.date', '>=', rec.date_from), ('service_id.date', '<=', rec.date_to),
                     ('labor_id', '=', labor.id), ('service_id.state', '=', 'confirmed')])
                no_days = rec.env['hr.temporary.service.attendance.line'].search_count(
                    [('service_id.date', '>=', rec.date_from), ('service_id.date', '<=', rec.date_to),
                     ('labor_id', '=', labor.id)])
                extra_hour_holiday = sum(attends.mapped('extra_hour_holiday'))
                extra_hour = sum(attends.mapped('extra_hour'))
                extra_pay = sum(attends.mapped('extra_pay'))
                if attends:
                    res.append((0, 0, {'labor_id': labor.id,
                                       'no_days': no_days,
                                       'extra_hour_holiday': extra_hour_holiday,
                                       'extra_hour': extra_hour,
                                       'extra_pay': extra_pay,
                                       'service_id': rec.id}))
            rec.line_ids = res

    def action_confirmed(self):
        self.write({'state': 'approved'})

    def _get_payment_count(self):
        for rec in self:
            rec.payment_count = rec.env['finance.approval'].search_count([('finapprov_id', '=', rec.id)])

    @api.model
    def create(self, vals):
        """
        A method to create sequence
        """
        sequences = self.env['ir.sequence'].sudo().search([('name', '=', 'Temporary Service Sequence')])
        # if vals['location'] == 'axxa':
        #     prefix = 'AXXA/TEP-Service/%(year)s/%(month)s/'
        #     for seq in sequences:
        #         seq.write({'prefix': prefix})
        # else:
        #     prefix = 'ELBAG/TEP-Service/%(year)s/%(month)s/'
        #     for seq in sequences:
        #         seq.write({'prefix': prefix})
        vals['reference'] = self.env['ir.sequence'].next_by_code('labor.sequence') or ('NEW')
        return super(HrTemporaryService, self).create(vals)

    @api.model
    def default_get(self, fields):
        res = super(HrTemporaryService, self).default_get(fields)
        res['working_hours'] = float(self.env['ir.config_parameter'].sudo().get_param('hr_temporary_service.working_hours'))
        return res

    def create_finance_approval(self):

        fin_id = self.env['finance.approval'].create({
            'reason': self.name,
            'fa_date': self.date_from,
            'request_amount': self.total_amount,
            'requester': self.env.user.name,
            'finapprov_id': self.id

        })
        self.payment_done = True

    def action_finace(self):
        actions = self.env.ref('is_accounting_approval_15.action_fa').read()[0]
        actions['context'] = {'default_finapprov_id': self.id}
        actions['domain'] = [('finapprov_id', '=', self.id)]
        return actions

    def action_compute_wage(self):
        for rec in self:
            if rec.pay_type == 'days':
                for line in rec.line_ids:
                    line.wage = (line.no_days * rec.wage_day) + line.extra_pay + line.mount_hour
            if rec.pay_type == 'hours':
                for line in rec.line_ids:
                    line.wage = (line.no_hours * rec.wage_hour) + line.extra_pay + line.mount_hour

    # ******** Compute work days for labor **********
    @api.onchange('date_from', 'date_to')
    def _compute_work_days(self):
        if self.date_from and self.date_to:
            day = self.date_to - self.date_from
            self.work_day = day.days


class HrTemporaryServiceLine(models.Model):
    _inherit = "temporary.service.line"
    labor_id = fields.Many2one("res.partner", string="Name", required=False,
                               domain="[('labor','=',True)]")
    # location = fields.Selection(string="Location", selection=[('axxa', 'Axxa'), ('elbagir', 'Elbagir'), ],
    #                             )

    def _get_no_days(self):
        for rec in self:
            if rec.service_id:
                rec.no_days = rec.service_id.work_day
            else:
                rec.no_days = 0

    extra_hour = fields.Float("Extra Hours")
    extra_hour_holiday = fields.Float("Extra Holiday Hours")
    mount_hour = fields.Float("Price of Hours", compute='_compute_price_hour')
    mount_hour_holiday = fields.Float("Price of Hours", compute='_compute_price_hour')
    no_days = fields.Integer(string="Number Of Days", required=False, default=_get_no_days)
    # day_rate = fields.Float(string="Wage", required=False)
    day_rate = fields.Float(string="Wage", required=False, related='job_type_id.day_rate')
    wage = fields.Float(string="Wage", required=False, compute='_compute_wage')
    job_type_id = fields.Many2one(comodel_name="labor.job.type", string="Job", required=False,
                                  related='labor_id.job_type_id')

    ov_hour_in_work_day_rate = fields.Float(string='Hour In a Work Day:')
    ov_hour_in_holiday_rate = fields.Float(string='Hour In a Holiday:')
    working_hours = fields.Float(string='Working Hours:')

    @api.depends('ov_hour_in_holiday_rate', 'ov_hour_in_work_day_rate', 'working_hours', 'day_rate')
    def _compute_price_hour(self):
        for rec in self:
            if rec.working_hours > 0:
                rec.mount_hour = (rec.day_rate / rec.working_hours) * rec.ov_hour_in_work_day_rate
                rec.mount_hour_holiday = (rec.day_rate / rec.working_hours) * rec.ov_hour_in_holiday_rate
            else:
                rec.mount_hour = 0
                rec.mount_hour_holiday = 0

    @api.depends('day_rate', 'no_days', 'extra_hour_holiday', 'extra_hour', 'extra_pay', 'mount_hour',
                 'mount_hour_holiday')
    def _compute_wage(self):
        for rec in self:
            rec.wage = (rec.day_rate * rec.no_days) + (rec.extra_hour_holiday * rec.mount_hour_holiday) + (
                    rec.extra_hour * rec.mount_hour) + rec.extra_pay

    @api.model
    def default_get(self, fields):
        res = super(HrTemporaryServiceLine, self).default_get(fields)
        res['ov_hour_in_work_day_rate'] = float(
            self.env['ir.config_parameter'].sudo().get_param('hr_temporary_service.ov_hour_in_work_day_rate'))
        res['ov_hour_in_holiday_rate'] = float(
            self.env['ir.config_parameter'].sudo().get_param('hr_temporary_service.ov_hour_in_holiday_rate'))
        res['working_hours'] = float(self.env['ir.config_parameter'].sudo().get_param('hr_temporary_service.working_hours'))
        return res


class FinanceApproval(models.Model):
    _inherit = "finance.approval"

    finapprov_id = fields.Many2one('hr.temporary.service', string="Finance Approval")


# class HrServicePartner(models.TransientModel):
#     _inherit = 'hr.service.partner'

#     def _get_available_partner(self):
#         temp_active = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
#         return [('labor', '=', True), ('location', '=', temp_active.location)]

#     def get_partner(self):
#         rec = self.env['temporary.service.line'].browse(self._context.get('active_ids', []))
#         temp_active = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
#         temp_active.line_ids.unlink()
#         for l in self.partner_ids:
#             new_line = self.env['temporary.service.line'].create({
#                 'labor_id': l.id,
#                 'service_id': temp_active.id,
#                 'no_days': temp_active.work_day,
#             })


class ZawayResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ov_hour_in_work_day_rate = fields.Float(string='Hour In a Work Day:',
                                            config_parameter='hr_temporary_service.ov_hour_in_work_day_rate')
    ov_hour_in_holiday_rate = fields.Float(string='Hour In a Holiday:',
                                           config_parameter='hr_temporary_service.ov_hour_in_holiday_rate')
    working_hours = fields.Float(string='Working Hours:', config_parameter='hr_temporary_service.working_hours')

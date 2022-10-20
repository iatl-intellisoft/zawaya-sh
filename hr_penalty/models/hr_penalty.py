# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, time, timedelta
from odoo.tools.translate import html_translate

class HrPenalty(models.Model):
    _name = "hr.penalty"
    _inherit = ['mail.thread']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', )
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',store=True)
    job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    employee_active = fields.Boolean(string='employee active', default=True)
    violation_id = fields.Many2one('hr.violation', string="violation", tracking=5)
    punishment_ids = fields.Many2one('hr.punishment', compute="_compute_punishment_id", store=True, string='Punishment',
                                     tracking=5, stroe=True)
    Date = fields.Date(string='Date', default=fields.Date.context_today,
                       readonly=True)
    violation_date = fields.Date(string='Violation Date', default=fields.Date.context_today,
                                 tracking=5)
    # deduction_id = fields.Many2one('hr.deduction', string='Deduction', readonly=True, tracking=5)
    amount = fields.Float(string='Amount', compute='_compute_amount')
    last_penalty_id = fields.Many2one('hr.penalty', string='last_penalty', ondelete='set null', )
    punishment_type = fields.Selection(selection=[
        ('warning', 'Warning'),
        ('penalty', 'Penalty'),
        ('suspend', 'Suspend'),
        # ('terminate', 'Terminate')
        ], related="punishment_ids.punishment_type", string='Punishment Type',
        default='warning')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('dept_approve', 'Waiting Department Manager approval'),
        ('hr_approve', 'Waiting HR approval'),
        ('gm_approve', 'Waiting GM approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel','Cancel'),
    ], string="State", default='draft', tracking=5, copy=False)
    deduct_id = fields.Many2one(string='Deduct Create', tracking=5)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    penalty_template_id = fields.Many2one('mail.template', related='company_id.penalty_template_id',
                                          string='Penalty Template')
    website_description = fields.Html('Penalty Template', sanitize_attributes=False, translate=html_translate,
                                      compute="get_penalty_template")
    hours = fields.Float(string='Hours')
    deduct_by = fields.Selection(related='punishment_ids.deduct_by', string="Deduct By")
    days = fields.Float(string='Days')
    # service_termination_id = fields.Many2one('hr.service.termination', string='Servise Termination Ref')
    next_punshment_id = fields.Many2one('hr.punishment', compute="_compute_next_punishment_id",
                                        string='Next Punishment',
                                        tracking=5)
    confirming_employee_id = fields.Many2one('hr.employee', string='Confirming Employee')
    approving_employee_id = fields.Many2one('hr.employee', string='Approving Employee')
    mail_track = fields.Many2one('mail.message', string="Mail tracking")
    requestor_id = fields.Many2one('res.users', string='Requestor', default=lambda self: self.env.user)
    total_deduction = fields.Integer(compute='_count_deductions')
    first_witness = fields.Many2one('res.partner')
    second_witness = fields.Many2one('res.partner')
    required_deduction = fields.Boolean(related="punishment_ids.required_deduction")
    cancel_reason = fields.Text()


    def _count_deductions(self):
        self.total_deduction = 0
        if self.punishment_ids:
            if self.punishment_ids.punishment_type == 'penalty':
                deductions = self.env['hr.deduction'].search([('penalty_id','=',self.id)])
                if deductions:
                    for ded in deductions:
                        self.total_deduction += ded.amount


    @api.onchange('punishment_ids')
    def return_hours(self):
        """
        A method to compute punishment hours
        """
        self.hours = self.punishment_ids.hours

    @api.onchange('punishment_ids')
    def return_days(self):
        """
        A method to compute punishment days
        """
        self.days = self.punishment_ids.days

    @api.depends('punishment_ids')
    def _compute_next_punishment_id(self):
        """
        A method to compute next punishment sequence
        """
        next_punshment_id = False
        for rec in self:
            if rec.violation_id and rec.punishment_ids:
                # 1) Increment the sequence by 1
                next_seq_obj = rec.violation_id.line_ids.search(
                    [('violation_id', '=', rec.violation_id.id),
                    ('punishment_ids', '=', rec.punishment_ids.id)], limit=1) or False
                if next_seq_obj:
                    next_pun_seq = next_seq_obj.sequence + 1
                    # 2) Fiend the punshment that it's sequence equal to or greater than next_pun_seq 
                    next_pun_obj = rec.violation_id.line_ids.search(
                        [('violation_id', '=', rec.violation_id.id),
                        ('sequence', '>=', next_pun_seq)], limit=1)
                    # 3) Fined and return the id of the next punshment if found
                    next_punshment_id = next_pun_obj and next_pun_obj.punishment_ids.id or False
        rec.next_punshment_id = next_punshment_id

    def action_confirm(self):
        """
        A method to confirm penalty
        """
        self.write({'state': 'submit'})
        user_id = self.env.user.id
        # 1) Get the employee object
        employee_obj = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
        # Another way of getting the employee 
        # resource = self.env['resource.resource'].search([('user_id','=',self.env.user.id)])
        # employee_obj = self.env['hr.employee'].search([('resource_id','=',resource.id)])
        # 2) Get the employee id
        employee_id = employee_obj.id
        # 3) Assign the employee to the related user
        self.confirming_employee_id = employee_id

    def action_draft(self):
        """
        A method to set penalty draft
        """
        self.write({'state': 'draft'})

    def action_dept_approve(self):
        self.write({'state': 'dept_approve'})

    def action_hr_approve(self):
        self.write({'state': 'hr_approve'})

    def action_gm_approve(self):
        self.write({'state': 'gm_approve'})

    def action_approve(self):
        """
        A method to approve penalty
        """
        user_id = self.env.user.id
        # 1) Get the employee object
        employee_obj = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
        # 2) Get the employee id
        employee_id = employee_obj.id
        # 3) Assign the employee to the related user
        self.approving_employee_id = employee_id

        puishment_type = self.punishment_ids.punishment_type
        if puishment_type == "suspend":
            self.employee_id.active = False
            self.employee_active = self.employee_id.active
            self.write({'state': 'approve'})

        # elif puishment_type == "terminate":
        #     # hr_service_obj = self.env['hr.service.termination']
        #     # service_termination_id = hr_service_obj.create({
        #     #     'employee_id': self.employee_id.id,
        #     #     'termination_date': self.Date,
        #     #     'working_days': 30,
        #     #     'reason_id': self.punishment_ids.termination_reason_id.id
        #     # })
        #     # self.service_termination_id = service_termination_id
        #     self.write({'state': 'approve'})

        elif puishment_type == "penalty":
            deduction_obj = self.env['hr.deduction']
            punishment_type = self.punishment_ids.deduct_type_id
            deduct_id = deduction_obj.create({
                'employee_id': self.employee_id.id,
                'type_id': punishment_type.id,
                'deducted_by': 'amount',
                'amount': self.amount,
                'penalty_id':self.id
            })
            # self.deduction_id = deduct_id.id
            self.write({'state': 'approve'})
            self.message_post(body=_("Deduction has been created for this penalty:%s")%(deduct_id.name))
        else:
            self.write({'state': 'approve'})
            
    def action_refuse(self):
        """
        A method to refuse penalty
        """
        self.write({'state': 'refuse'})

    @api.depends('punishment_ids')
    def unsuspend_employee(self):
        """
        A method to unsuspend employee
        """
        if not self.employee_id.active:
            self.employee_id.active = True
            self.employee_active = self.employee_id.active

    @api.depends('penalty_template_id', 'penalty_template_id.body_html')
    def get_penalty_template(self):
        """
        A method to get penalty template
        """
        for rec in self:
            rec.website_description += rec.website_description
            if rec.penalty_template_id and rec.id:
                fields = ['body_html']
                template_values = rec.penalty_template_id.generate_email([rec.id], fields=fields)
                rec.website_description = template_values[rec.id].get('body_html')

    @api.depends('punishment_ids')
    def _compute_amount(self):
        """
        A method to compute penalty amount
        """
        for record in self:
            record.amount += record.amount
            if record.punishment_ids:
                puishment_type = record.punishment_ids.punishment_type
                if puishment_type == "penalty":
                    deduct_by = record.punishment_ids.deduct_by
                    if deduct_by == "hours" or deduct_by == "days":
                        rule_amount = record.punishment_ids.rule_id.compute_rule_amount(record.employee_id)
                        if deduct_by == "hours":
                            record.amount = rule_amount * record.hours
                        else:
                            record.amount = rule_amount * record.days
                    elif deduct_by == "fix_amount":
                        record.amount = record.punishment_ids.fix_amount

    @api.depends('employee_id', 'violation_date', 'violation_id')
    def _compute_punishment_id(self):
        """TO DO"""
        for rec in self:
            last_penalty = False
            if rec.violation_id and rec.employee_id and rec.violation_date:
                last_penalty = rec.env['hr.penalty'].search(
                    [('state', '=', 'approve'),
                    ('violation_id', '=', rec.violation_id.id), 
                    ('employee_id', '=', rec.employee_id.id),
                    ('violation_date', '<=', rec.violation_date)], 
                    order="violation_date desc")
            if last_penalty:
                old_penalty = last_penalty[0]
                self.last_penalty_id = old_penalty
                old_punishment = old_penalty.punishment_ids
                old_violation = old_penalty.violation_id
                punishment_period = old_punishment.period
                old_violation_date = datetime.strptime(str(old_penalty.violation_date), '%Y-%m-%d')
                current_violation_date = datetime.strptime(str(rec.violation_date), '%Y-%m-%d')
                period = relativedelta(current_violation_date, old_violation_date)
                month = period.months
                next_seq = 0
                if month >= punishment_period:
                    rec.punishment_ids = old_punishment
                elif month < punishment_period or month is None:
                    next_seq_obj = old_violation.line_ids.search(
                        [('punishment_ids', '=', old_punishment.id)],limit=1)
                    next_seq = next_seq_obj and next_seq_obj.sequence + 1

                    if old_violation == self.violation_id:
                        violation_line = rec.env['hr.violation.line'].search(
                            [('sequence', '>=', next_seq), 
                            ('violation_id', '=', old_violation.id)], limit=1)
                        if violation_line:
                            rec.punishment_ids = violation_line.punishment_ids.id
                        else:
                            violation_line = rec.env['hr.violation.line'].search(
                                [('violation_id', '=', old_violation.id)],
                                order="sequence desc", limit=1)

                            if violation_line:
                                rec.punishment_ids = violation_line.punishment_ids.id
                    else:
                        violation_line = rec.env['hr.violation.line'].search(
                            [('sequence', '=', next_seq), 
                            ('violation_id', '=', self.violation_id.id)], limit=1)
                        if violation_line:
                            rec.punishment_ids = violation_line.punishment_ids.id

                        else:
                            violation_line = rec.env['hr.violation.line'].search(
                                [('violation_id', '=', self.violation_id.id)],
                                order="sequence desc", limit=1)

                            if violation_line:
                                rec.punishment_ids = violation_line.punishment_ids.id
            else:
                violation_line = rec.env['hr.violation.line'].search(
                    [('violation_id', '=', rec.violation_id.id)],order="sequence ASC", limit=1)
                if violation_line:
                    rec.punishment_ids = violation_line.punishment_ids.id

    def get_sum_amount(self):
        """
        A method to get sum penalty amount
        """
        sum_amount = self.hr_penalty
        hr_penalty = self.env['hr.penalty']
        hr_penalty.search([('company_id', '=', 'company_id')])
        return sum_amount

    def unlink(self):
        """
        A method to delete penalty in draft status
        """
        for order in self:
            if order.state not in ('draft',):
                raise UserError(_('You can not delete record not in draft state.'))
        return super(HrPenalty, self).unlink()

    def action_mail_send(self):
    # self.write({'state': 'sent'})

        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_penalty', 'penalty_teamplate_id')[1]
        except ValueError:
            template_id = False
       
        ctx = dict(self.env.context or {})
        ctx.update({
        'default_model': 'hr.penalty',
        'default_res_id': self.ids[0],
        'default_use_template': bool(template_id),
        'default_template_id': template_id,
        'default_composition_mode': 'comment',
        'force_email': True
        })

        return {
        'name': _('Penalty Email'),
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'mail.compose.message',
        'target': 'new',
        'context': ctx,
        }

    def penalty_cancel_wizard_action(self):
        return {
            'name': _('Cancel Penalty'),
            'res_model': 'penalty.cancel.wizard',
            'view_mode': 'form',
            'context': {
            'default_penalty_id': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class Employee(models.Model):
    _inherit = 'hr.employee'

    penalty_ids = fields.One2many('hr.penalty', 'employee_id', string='last_penalty',
                                  domain=[('state', '=', 'approve')])
    penalty_count = fields.Integer(compute='_compute_penalty_count', string='Penalty Count')

    def _compute_penalty_count(self):
        """
        A method to count all employees penalty without repetition.
        """
        penalty_data = self.env['hr.penalty'].sudo().read_group([('employee_id', 'in', self.ids)], ['employee_id'],
                                                                ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in penalty_data)
        for employee in self:
            employee.penalty_count = result.get(employee.id, 0)

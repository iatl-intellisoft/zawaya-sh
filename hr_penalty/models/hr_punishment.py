# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning
from odoo.exceptions import ValidationError

class HrPunishment(models.Model):
    _name = 'hr.punishment'

    name = fields.Char('Name')
    punishment_type = fields.Selection(selection=[
        ('warning', 'Warning'),
        ('penalty', 'Penalty'),
        ('suspend', 'Suspend'),
        ('terminate', 'Terminate')
    ], string='Punishment Type', default='warning')
    deduct_type_id = fields.Many2one('hr.deduct.conf', domain=[('deducted_by', '=', 'amount')], string='Deduct Type')
    deduct_by = fields.Selection(selection=[('hours', 'Hours'), ('days', 'Days'), ('fix_amount', 'Fix Amount')],
                                 default='fix_amount', string='Deduct By')
    hours = fields.Float(string='Hours')
    days = fields.Float(string='Days')
    fix_amount = fields.Float(string='Fix Amount', )
    period = fields.Integer(string='Period (Months)', default=1)
    # termination_reason_id = fields.Many2one('hr.service.termination.reasons', string='Termination Reason ',
    #                                         ondelete='set null', )
    rule_id = fields.Many2one(
        string='Salary rule',
        comodel_name='hr.salary.rule',
        ondelete='set null',
    )
    required_deduction = fields.Boolean(default=False)

class HrViolation(models.Model):
    _name = 'hr.violation'

    name = fields.Char('Name')
    line_ids = fields.One2many('hr.violation.line', 'violation_id', string='line id ')


class HrViolationLine(models.Model):
    _name = 'hr.violation.line'

    violation_id = fields.Many2one('hr.violation', string="violation")
    sequence = fields.Integer(string='sequence', )
    punishment_ids = fields.Many2one('hr.punishment', string='Punishment')

    @api.constrains('sequence')
    def _check_sequence(self):
        for rec in self:
            if rec.sequence < 0:
                raise ValidationError(_("Sequence is less than zero!"))
    _sql_constraints = [
        ('sequense_uniq', 'unique(violation_id,sequence)', 'Sequence must be unique per violation!'),
    ]

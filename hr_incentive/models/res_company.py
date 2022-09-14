# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    incentive_double_validation = fields.Selection([
        ('one_step', 'Confirm Staff Payments in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm Staff Payments')
    ], string="Levels of Approvals", default='one_step',
        help="Provide a double validation mechanism for purchases")
    incentive_double_validation_amount = fields.Monetary(string='Staff Payments Double validation amount', default=5000,
                                                         help="Minimum amount for which a double validation is required")
    incentive_template_id = fields.Many2one('mail.template', string='Employee Payments Template',
                                            domain="[('model','=','hr.incentive')]")

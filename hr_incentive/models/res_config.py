# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,
                                          help='Utility field to express amount currency')
    incentive_double_validation = fields.Selection(related='company_id.incentive_double_validation',
                                                   string="Staff Payments Levels of Approvals *", readonly=False)
    incentive_double_validation_amount = fields.Monetary(related='company_id.incentive_double_validation_amount',
                                                         string="Staff Payments Double validation amount *",
                                                         currency_field='company_currency_id', readonly=False)
    incentive_template_id = fields.Many2one('mail.template', string='Staff Payments Template',
                                            related='company_id.incentive_template_id', readonly=False)

# -*- coding: utf-8 -*-


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    compute_day = fields.Integer(string="Days",related ='company_id.compute_day',readonly=False)



class ResCompanySaleCustom(models.Model):

    _inherit = 'res.company'

    compute_day = fields.Integer(string="Days")

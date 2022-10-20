# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import models, fields, api

class hr_contract(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection(selection_add=[
        ('service_termination', 'Waiting Service Termination'), 
        ('terminated', 'Terminated')
    ])
   

class hr_contract_history(models.Model):
    _inherit = 'hr.contract.history'

    state = fields.Selection(selection_add=[
        ('service_termination', 'Waiting Service Termination'), 
        ('terminated', 'Terminated')
    ])
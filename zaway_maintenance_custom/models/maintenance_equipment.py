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
from odoo import tools


class MaintenanceeQuipmentInherit(models.Model):
    _inherit = 'maintenance.equipment'

    manufacture_company  = fields.Char(string="The Manufacture Company")
    code = fields.Char(string="Code")


class MaintenanceStageInherit(models.Model):
    _inherit = 'maintenance.stage'


    in_progress = fields.Boolean(string="In Progress")
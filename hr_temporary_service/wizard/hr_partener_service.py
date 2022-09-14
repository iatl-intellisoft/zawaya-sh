# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from collections import defaultdict
from datetime import datetime, date, time
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrServicePartner(models.TransientModel):
    _name = 'hr.service.partner'

    def _get_available_partner(self):
        return [('id', '!=', False)]

    def _get_partner(self):
        # YTI check dates too
        return self.env['hr.labor'].search(self._get_available_partner())

    partner_ids = fields.Many2many('hr.labor', string='partners',default=lambda self: self._get_partner(), required=True)

    def get_partner(self):
        rec = self.env['temporary.service.line'].browse(self._context.get('active_ids', []))
        temp_active = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
        for l in self.partner_ids:
            new_line =rec.create({
                    'labor_id':l.id,
                    'function':l.job_id.id,
                    'department_id':l.department_id.id,
                    'service_id':temp_active.id,
                    })

            
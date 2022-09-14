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


class HrServiceRefuse(models.TransientModel):
    _name = 'hr.service.refuse'

    reason = fields.Text(string='Reason')

    def action_service_refuse(self):
        if self._context.get('active_model') == 'hr.temporary.service':
            rec = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
            refuse_user = self.env.user.name +' '+':'+' '+ self.reason
            rec.write({'note': refuse_user})
            # if self._context.get("cancel") == True:
            rec.write({'state': 'refuse'})
            # elif self._context.get("draft") == True:
            #     rec.write({'state': 'draft'})

    # def get_partner(self):
    #     rec = self.env['temporary.service.line'].browse(self._context.get('active_ids', []))
    #     temp_active = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
    #     for l in self.partner_ids:
    #         new_line = rec.create({
    #             'labor_id': l.id,
    #             'function': l.job_id.id,
    #             'department_id': l.department_id.id,
    #             'service_id': temp_active.id,
    #         })


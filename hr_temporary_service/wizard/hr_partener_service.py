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
        temp_active = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
        return [('labor', '=', True)]
        # ('location', '=', temp_active.location)

    # def _get_available_partner(self):
    #     return [('labor', '=', True)]

    def _get_partner(self):
        # YTI check dates too
        return self.env['res.partner'].search(self._get_available_partner())

    partner_ids = fields.Many2many('res.partner', string='partners',default=lambda self: self._get_partner(), required=True,domain=[('labor','=',True)])

    # def get_partner(self):
    #     rec = self.env['temporary.service.line'].browse(self._context.get('active_ids', []))
    #     temp_active = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
    #     for l in self.partner_ids:
    #         new_line =rec.create({
    #                 'labor_id':l.id,
    #                 'service_id':temp_active.id,
    #                 })

    def get_partner(self):
        rec = self.env['temporary.service.line'].browse(self._context.get('active_ids', []))
        temp_active = self.env['hr.temporary.service'].browse(self._context.get('active_ids', []))
        temp_active.line_ids.unlink()
        for l in self.partner_ids:
            new_line = self.env['temporary.service.line'].create({
                'labor_id': l.id,
                'service_id': temp_active.id,
                'no_days': temp_active.work_day,
            })


    def get_partner_line(self):
        rec = self.env['hr.temporary.service.attendance'].browse(self._context.get('active_ids', []))
        print('-------------------self.partner_ids',self.partner_ids)
        rec.attendance_ids.unlink()
        for l in self.partner_ids:
            new_line = self.env['hr.temporary.service.attendance.line'].create({
                'labor_id': l.id,
                'service_id': rec.id,
            })

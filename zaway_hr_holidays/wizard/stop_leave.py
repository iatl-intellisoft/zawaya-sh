# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from collections import namedtuple, defaultdict

from datetime import datetime, timedelta, time
from pytz import timezone, UTC

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

# Used to agglomerate the attendances in order to find the hour_from and hour_to
# See _compute_date_from_to
DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')


class StopHolidays(models.TransientModel):
	_name = 'hr.holidays.stop'

	stop_date = fields.Date(default=fields.Date.today())
	stop_reason = fields.Text(required=True)
	leave_id = fields.Many2one('hr.leave')

	def action_stop_apply(self):
		if self.stop_date < self.leave_id.request_date_to:
			print('\n\n\n in if')
			self.leave_id.action_refuse()
			self.leave_id.action_draft()
			self.leave_id.write({
				'old_end_date': self.leave_id.request_date_to,
				'old_number_of_days':self.leave_id.number_of_days,
				'stop_date':self.stop_date,
				'request_date_to':self.stop_date,
				'stop_reason':self.stop_reason,
				'stop': True,
			})
			self.leave_id.action_confirm()
			self.leave_id.first_confirm()
			self.leave_id.dept_confirm()
			self.leave_id.hr_confirm()
			self.leave_id.action_approve()
			self.leave_id.action_validate()
			# self.leave_id.write({
			# 	'state': 'stop',
			# })

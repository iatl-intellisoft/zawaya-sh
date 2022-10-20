# -*- coding: utf-8 -*-


from odoo import api, fields,models, _

class ReportCancelPenalty(models.TransientModel):
	_name = "penalty.cancel.wizard"

	cancel_reason = fields.Text(required=True)
	penalty_id = fields.Many2one('hr.penalty')


	def submit(self):
		if self.penalty_id:
			self.penalty_id.write({
				'cancel_reason': self.cancel_reason,
				'state':'cancel'
				})
			if self.penalty_id.deduct_id:
				self.penalty_id.deduct_id.write({
					'state':'cancel'
					})
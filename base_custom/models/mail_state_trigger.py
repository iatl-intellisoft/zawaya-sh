# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import models,api,fields

class MailTracking(models.Model):
	_inherit = 'mail.tracking.value'

	new_key_state = fields.Char('New Key State', readonly=1)

	# @api.model
	# def create_tracking_values(self, initial_value, new_value, col_name, col_info, track_sequence, model_name):
	# 	values = super(MailTracking, self).create_tracking_values(initial_value, new_value, col_name, col_info, track_sequence, model_name)
	# 	if col_info['type'] == 'selection':
	# 		values.update({'new_key_state': new_value})
	# 	return values

def getStateTriggers(self,model,res_id,states):
	track = []
	if model and res_id and states:
		for st in states:
			s0 = dict(self.fields_get(allfields=['state'])['state']['selection'])[str(st)]

			# s1 = dict(self.fields_get(allfields=['state'])['state']['selection'])[str(st[1])]

			st_value = self.env['mail.tracking.value'].sudo().search([('field', '=', 'state'),
																	  ('new_key_state', '=', st),
																	  ('mail_message_id.model', '=', model),
																	  ('mail_message_id.res_id', '=', res_id)], order='create_date ASC', limit=1)

			if st_value:
				track.append({'state': st,
							  'username':st_value.mail_message_id.author_id.name ,
							  'date': str(st_value.create_date.date())})

	return track

models.BaseModel.getStateTriggers = getStateTriggers

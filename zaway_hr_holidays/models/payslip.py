
from odoo import api, fields, models,_


class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	use_type = fields.Selection(
		string=u'Use Type',
		selection_add=[('time_off', 'Time Off')])


class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	time_off_amount = fields.Float( compute='_compute_time_off_amount')
	sell_timeoff_ids = fields.One2many('sell.time.off', 'payslip_id', string='Sell Time Off')
	
	@api.depends('employee_id')
	def _compute_time_off_amount(self): 
		amount = 0.0
		for record in self:
			if record.employee_id:
				ids = self.env['sell.time.off'].search([('employee_id','=',record.employee_id.id),
					('request_date','>=',record.date_from),('request_date','<=',record.date_to),
					('state','=','approve'),('paid', '=', False),('payslip_id','=',record.id)])
				for rec in ids:
					amount += rec.total_amount
			record.time_off_amount = amount

	def get_sell_time_off(self):
		array = []
		for record in self:
			record.sell_timeoff_ids.write({'payslip_id': False})
			record.sell_timeoff_ids = self.env['sell.time.off'].search(
				[('employee_id','=',record.employee_id.id),
				('request_date','>=',record.date_from),('request_date','<=',record.date_to),
				('state','=','approve'),('paid', '=', False)])
		return True

	def compute_sheet(self):
		self.get_sell_time_off()
		return super(HrPayslip, self.sudo()).compute_sheet()

	def action_payslip_done(self):
		"""
		A action_payslip_done method inherited and change overtime to paid to make overtime done.
		"""
		res = super(HrPayslip, self.sudo()).action_payslip_done()
		self.sell_timeoff_ids.write({'paid': True,'payslip_id':self.id})
		return res

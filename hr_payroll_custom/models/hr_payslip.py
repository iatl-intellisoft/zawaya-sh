
# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import api, fields, models,_
import xlsxwriter
import base64
from io import BytesIO

class HrPayrollRules(models.Model):
	_inherit = 'hr.salary.rule'

	company_id = fields.Many2one('res.company',default=lambda self : self.env.company)


class HrPayrollStructure(models.Model):
	_inherit = 'hr.payroll.structure'

	company_id = fields.Many2one('res.company',default=lambda self : self.env.company)
	
	@api.model
	def _get_default_rule_ids(self):
		return []

	rule_ids = fields.One2many(
		'hr.salary.rule', 'struct_id',
		string='Salary Rules', default=_get_default_rule_ids)

	

class HrPayroll(models.Model):
	_inherit = 'hr.payslip'


	def print_excel(self):
		file_name = _('Payslip Reports.xlsx')
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		excel_sheet = workbook.add_worksheet('الاجر الشهري')
		excel_sheet.right_to_left()
		header_format = workbook.add_format(
				{'align':'center','bold': True, 'font_color': 'black', 'bg_color': '#808080', 'border': 4})
		date_style = workbook.add_format({'text_wrap': True, 'border': 1,'num_format': 'dd-mm-yyyy'})
		base_format = workbook.add_format(
				{'font_color': 'black', 'border': 4})
		excel_sheet.set_column('B:B', 20, )
		excel_sheet.set_column('A:A', 5, )
		excel_sheet.set_column('C:T', 11, )

		excel_sheet.merge_range('R2:S2', 'حالة الأجر', header_format)
		
		row = 2
		col = 0

		excel_sheet.write(row, col, 'رقم', header_format)
		col += 1
		excel_sheet.write(row, col, 'الإسم', header_format)
		col += 1
		excel_sheet.write(row, col, 'المرتب', header_format)
		col += 1
		excel_sheet.write(row, col, 'الحافز', header_format)
		col += 1
		excel_sheet.write(row, col, 'الإجمالي', header_format)
		col += 1
		excel_sheet.write(row, col, 'ضمان إجتماعي', header_format)
		col += 1
		excel_sheet.write(row, col, 'تأمين صحي', header_format)
		col += 1
		excel_sheet.write(row, col, 'نصف الراتب', header_format)
		col += 1
		excel_sheet.write(row, col, 'نصف الراتب', header_format)
		col += 1
		excel_sheet.write(row, col, 'سلف', header_format)
		col += 1
		excel_sheet.write(row, col, 'غياب ', header_format)
		col += 1
		excel_sheet.write(row, col, 'تأخير ', header_format)
		col += 1
		excel_sheet.write(row, col, 'فطور ', header_format)
		col += 1
		excel_sheet.write(row, col, 'أيام خصم ', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي الاستقطاع ', header_format)
		col += 1
		excel_sheet.write(row, col, 'الصافي ', header_format)
		col += 1
		excel_sheet.write(row, col, 'التوقيع ', header_format)
		col += 1
		excel_sheet.write(row, col, 'نشط ', header_format)
		col += 1
		excel_sheet.write(row, col, 'موقوف ', header_format)
		col += 1


		col = 0
		row += 1
		counter = 1
		employee = self.employee_id
		payslip = self.env['hr.payslip'].search([('id','=',self.id)],limit=1)

		if payslip:
			excel_sheet.write(row, col, counter, base_format)
			col += 1
			excel_sheet.write(row, col, employee.name, base_format)
			col += 1
			excel_sheet.write(row, col, payslip.contract_id.wage, base_format)
			col += 1
			excel_sheet.write(row, col, payslip.contract_id.bouns, base_format)
			col += 1
			excel_sheet.write(row, col, payslip.contract_id.wage + payslip.contract_id.bouns, base_format)
			col += 1
			SI_id = payslip.line_ids.search([('code','=','SI'),('slip_id','=',payslip.id)]).ids
			SI = self.env['hr.payslip.line'].browse(max(SI_id)).total if SI_id else 0.0
			excel_sheet.write(row, col, SI, base_format)
			col += 1
			MED_INS_id = payslip.line_ids.search([('code','=','MED_INS'),('slip_id','=',payslip.id)]).ids
			MED_INS = self.env['hr.payslip.line'].browse(max(MED_INS_id)).total if MED_INS_id else 0.0
			excel_sheet.write(row, col, MED_INS, base_format)
			col += 1
			excel_sheet.write(row, col, payslip.contract_id.wage/2, base_format)
			col += 1
			excel_sheet.write(row, col, payslip.contract_id.wage/2, base_format)
			col += 1
			loan = payslip.total_amount_paid
			excel_sheet.write(row, col, loan, base_format)
			col += 1
			ABS_id = payslip.line_ids.search([('code','=','ABS'),('slip_id','=',payslip.id)]).ids
			ABS = self.env['hr.payslip.line'].browse(max(ABS_id)).total if ABS_id else 0.0
			excel_sheet.write(row, col, ABS, base_format)
			col += 1
			LATE_id = payslip.line_ids.search([('code','=','LATE'),('slip_id','=',payslip.id)]).ids
			LATE = self.env['hr.payslip.line'].browse(max(LATE_id)).total if LATE_id else 0.0
			excel_sheet.write(row, col, LATE, base_format)
			col += 1
			BREAKFAST_id = payslip.line_ids.search([('code','=','BREAKFAST'),('slip_id','=',payslip.id)]).ids
			BREAKFAST = self.env['hr.payslip.line'].browse(max(BREAKFAST_id)).total if BREAKFAST_id else 0.0
			excel_sheet.write(row, col, BREAKFAST, base_format)
			col += 1
			late_days = 0.0
			excel_sheet.write(row, col, late_days, base_format)
			col += 1
			total_ded = SI + MED_INS + loan + ABS + LATE + BREAKFAST
			excel_sheet.write(row, col, total_ded, base_format)
			col += 1
			NET_id = payslip.line_ids.search([('code','=','NET'),('slip_id','=',payslip.id)]).ids
			NET = self.env['hr.payslip.line'].browse(max(NET_id)).total if NET_id else 0.0			
			excel_sheet.write(row, col, NET, base_format)
			col += 1

			col = 0
			row += 1
			counter += 1

		workbook.close()
		file_download = base64.b64encode(fp.getvalue())
		fp.close()
		wizardmodel = self.env['employee.payslip.report.excel']
		res_id = wizardmodel.create({'name': file_name, 'file_download': file_download})
		return {
				'name': 'Files to Download',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'employee.payslip.report.excel',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'res_id': res_id.id,
			}

class HrPayrollInputs(models.Model):
	_inherit = 'hr.payslip.input.type'

	company_id = fields.Many2one('res.company',default=lambda self : self.env.company)

class HrPayrollParameter(models.Model):
	_inherit = 'hr.rule.parameter'

	company_id = fields.Many2one('res.company',default=lambda self : self.env.company)

class HrPayrollParameterValue(models.Model):
	_inherit = 'hr.rule.parameter.value'

	company_id = fields.Many2one('res.company',default=lambda self : self.env.company)
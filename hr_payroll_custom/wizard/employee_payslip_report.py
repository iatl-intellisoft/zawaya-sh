

# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
import xlsxwriter
import base64
from io import BytesIO

class PayslipReport(models.TransientModel):
	_name = "employee.payslip.wizard"

	date = fields.Date(required=True,default=fields.Date.today())
	# date_to = fields.Date(required=True)
	department_ids = fields.Many2many('hr.department',string="Departments")
	

	def print(self):
		file_name = _('Departments Payslip Report.xlsx')
		fp = BytesIO()
		workbook = xlsxwriter.Workbook(fp)
		excel_sheet = workbook.add_worksheet('الاجر الشهري للاقسام')
		excel_sheet.right_to_left()
		header_format = workbook.add_format(
				{'align':'center','bold': True, 'font_color': 'black', 'bg_color': '#808080', 'border': 4})
		date_style = workbook.add_format({'text_wrap': True, 'border': 1,'num_format': 'dd-mm-yyyy'})
		base_format = workbook.add_format(
				{'font_color': 'black', 'border': 4})
		excel_sheet.set_column('B:B', 20, )
		excel_sheet.set_column('A:A', 5, )
		excel_sheet.set_column('C:T', 11, )
		
		row = 2
		col = 0

		excel_sheet.write(row, col, 'رقم', header_format)
		col += 1
		excel_sheet.write(row, col, 'القسم', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي المرتبات', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي الحوافز', header_format)
		col += 1
		excel_sheet.write(row, col, 'الإجمالي', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي ضمان إجتماعي', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي تأمين صحي', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي نصف الراتب', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي السلف', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي استقطاع الغياب ', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي استقطاع التأخير ', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي استقطاع الفطور ', header_format)
		col += 1
		excel_sheet.write(row, col, 'إجمالي الاستقطاع ', header_format)
		col += 1
		excel_sheet.write(row, col, 'الصافي ', header_format)
		col += 1
		excel_sheet.write(row, col, 'التوقيع ', header_format)
		col += 1
		excel_sheet.write(row, col, 'موقوف ', header_format)
		col += 1
		
		col = 0
		row += 1
		counter = 1
		departments = self.env['hr.department'].search([])

		if self.department_ids:
			departments = self.department_ids

		for dept in departments:
			dept_emps = self.env['hr.employee'].search([('department_id','=',dept.id)])
			
			total_wage = 0.0
			total_bouns = 0.0
			total_si = 0.0
			total_med_ins = 0.0
			half_wage = 0.0
			total_loan = 0.0
			total_abs = 0.0
			total_late = 0.0
			total_breakfast = 0.0
			total_ded = 0.0
			total_net = 0.0
			for emp in dept_emps:
				payslip = self.env['hr.payslip'].search([('employee_id','=',emp.id),
				('state','=','paid'),
				('date_from','<=',self.date),('date_to','>=',self.date)
				])

				if payslip:
					total_wage += payslip.contract_id.wage
					total_bouns += payslip.contract_id.bouns

					SI_id = payslip.line_ids.search([('code','=','SI'),('slip_id','=',payslip.id)]).ids
					SI = self.env['hr.payslip.line'].browse(max(SI_id)).total if SI_id else 0.0
					total_si += SI

					MED_INS_id = payslip.line_ids.search([('code','=','MED_INS'),('slip_id','=',payslip.id)]).ids
					MED_INS = self.env['hr.payslip.line'].browse(max(MED_INS_id)).total if MED_INS_id else 0.0
					total_med_ins += MED_INS
					
					half_wage+= payslip.contract_id.wage/2

					total_loan += payslip.search([('id','=',payslip.id)]).total_amount_paid

					ABS_id = payslip.line_ids.search([('code','=','ABS'),('slip_id','=',payslip.id)]).ids
					ABS = self.env['hr.payslip.line'].browse(max(ABS_id)).total if ABS_id else 0.0
					total_abs += ABS

					LATE_id = payslip.line_ids.search([('code','=','LATE'),('slip_id','=',payslip.id)]).ids
					LATE = self.env['hr.payslip.line'].browse(max(LATE_id)).total if LATE_id else 0.0
					total_late += LATE

					BREAKFAST_id = payslip.line_ids.search([('code','=','BREAKFAST'),('slip_id','=',payslip.id)]).ids
					BREAKFAST = self.env['hr.payslip.line'].browse(max(BREAKFAST_id)).total if BREAKFAST_id else 0.0
					total_breakfast += BREAKFAST

					total_ded = total_si + total_med_ins + total_loan + total_abs + total_late + total_breakfast

					NET_id = payslip.line_ids.search([('code','=','NET'),('slip_id','=',payslip.id)]).ids
					NET = self.env['hr.payslip.line'].browse(max(NET_id)).total if NET_id else 0.0			
					total_net += NET

			total = total_wage + total_bouns
			excel_sheet.write(row, col, counter, base_format)
			col += 1
			excel_sheet.write(row, col, dept.name, base_format)
			col += 1
			excel_sheet.write(row, col, total_wage, base_format)
			col += 1
			excel_sheet.write(row, col, total_bouns, base_format)
			col += 1
			excel_sheet.write(row, col, total, base_format)
			col += 1
			excel_sheet.write(row, col, total_si, base_format)
			col += 1
			excel_sheet.write(row, col, total_med_ins, base_format)
			col += 1
			excel_sheet.write(row, col, half_wage, base_format)
			col += 1
			excel_sheet.write(row, col, total_loan, base_format)
			col += 1
			excel_sheet.write(row, col, total_abs, base_format)
			col += 1
			excel_sheet.write(row, col, total_breakfast, base_format)
			col += 1
			excel_sheet.write(row, col, total_late, base_format)
			col += 1
			excel_sheet.write(row, col, total_ded, base_format)
			col += 1
			excel_sheet.write(row, col, total_net, base_format)
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



class PayslipReportWizexel(models.TransientModel):
	_name = 'employee.payslip.report.excel'

	name = fields.Char('File Name', size=256, readonly=True)
	file_download = fields.Binary('File to Download', readonly=True)

# -*- coding: utf-8 -*-
from odoo import models, fields, api,tools, _
from odoo.tools import float_round
from odoo.exceptions import UserError, Warning
from datetime import datetime,date


class DailySalesReport(models.AbstractModel):
    _name = 'report.zaway_sale_custom.daily_sales_template'

    def _get_header_info(self, data):
        date_from = data['date_from']
        date_to = data['date_to']
        company_id = data['comp']

        return {
            'date_from': date_from,
            'date_to': date_to,
            'company_id': company_id,

        }

    def _get_daily_sales(self, data):

        sale_list =[]

        if data['date_from'] > data['date_to']:
            raise UserError(_("يجب إدخال تاريخ بدء أقل من تاريخ الانتهاء."))


        invoices = self.env['account.move'].search([
            ('invoice_date', '>=', data['date_from']),
            ('invoice_date', '<=',data['date_to']),
            ('move_type','=','out_invoice'),
            ('state','=','posted'),
            ('payment_state','in',['paid','partial']),
            ('company_id','=',data['comp'])])

        payment = self.env['account.payment'].search([])
        payment.mapped('move_id')


        for inv in invoices:
            check = 0
            cash = 0
            total_invoice = 0
            for pay in payment.filtered(lambda r:r.ref == inv.name):
                
                if pay.journal_id.type == 'bank':
                    check+= pay.amount
                if pay.journal_id.type == 'cash':
                    cash+= pay.amount

                total_invoice+= check + cash

            sale_list.append({
                'date': inv.invoice_date,
                'customer': inv.partner_id.name,
                'no': inv.name,
                'check': check,
                'cash': cash,
                'total_invoice': inv.amount_total
                })
        return sale_list

    @api.model
    def _get_report_values(self, docids, data=None):
        data['records'] = self.env['account.move'].browse(data)
        docs = data['records']
        invoice_report = self.env['ir.actions.report']._get_report_from_name('zaway_sale_custom.daily_sales_template')
        docargs = {

            'data': data,
            'docs': docs,
        }
        return {
            'doc_ids': self.ids,
            'doc_model': invoice_report.model,
            'docs': data,
            'get_info': self._get_header_info(data),
            'get_report': self._get_daily_sales(data),
        }
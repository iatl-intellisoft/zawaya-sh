# -*- coding: utf-8 -*-
from odoo import models, fields, api,tools, _
from odoo.tools import float_round
from odoo.exceptions import UserError, Warning
from datetime import datetime,date


class ChequeReport(models.AbstractModel):
    _name = 'report.zaway_account_custom.cheque_template'

    def _get_header_info(self, data):
        date_from = data['date_from']
        date_to = data['date_to']
        # under_collection = data['under_collection']
        # in_bank = data['in_bank']
        # rejected = data['rejected']
        # return_to = data['return_to']
        # out_standing = data['out_standing']
        # withdrawal = data['withdrawal']
        # done = data['done']
        # cancel = data['cancel']
        customer_name = data['customer_name']
        customer_id = data['customer_id']
        state = data['state']

        return {
            'date_from': date_from,
            'date_to': date_to,
            'customer_id': customer_id,
            'customer_name': customer_name,
            # 'under_collection': under_collection,
            # 'rejected': rejected,
            # 'in_bank' : in_bank,
            # 'return_to': return_to,
            # 'out_standing': out_standing,
            # 'withdrawal': withdrawal,
            # 'done': done,
            # 'cancel': cancel,
            'state': state,
            # 'company_id': company_id,

        }

    def _get_cheque(self, data):

        # customer_list =[]
        # check_list = []

        if data['date_from'] > data['date_to']:
            raise UserError(_("You must enter a start date less than the end date."))


        check_followups = self.env['check_followups.check_followups'].search([
            ('Date', '>=', data['date_from']),
            ('Date', '<=',data['date_to'])])


        if data['date_from'] and data['date_to'] and not data['customer_id']:
            customers = self.env['res.partner'].search([])
            customer_list =[]
            print("_____nnn_______________________________",customers)
            for custom in customers:
                data_list = []
                lines_list = []

                for check in check_followups.filtered(lambda r:r.account_holder == custom):
                    print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCc",check)
                    operation_line = []
                    operation_line = [check.state,check.Date,check.check_no,check.payment_id.check_date,check.payment_id.journal_id.name,check.amount]
                    lines_list.append(operation_line)
                
                lines_dict = {}
                for rec in lines_list:

                    if rec[0] in lines_dict:
                        lines_dict[rec[0]].append([rec[1],rec[2],rec[3],rec[4],rec[5]])

                    else:

                        lines_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]


                
                # if lines_dict:
                #     customer_list.append({
                #         'custom':custom.name,
                #         'data_list':lines_dict,                    
                #         })

            # if lines_dict:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11lines_dict",lines_dict)
            return lines_dict

        if data['date_from'] and data['date_to'] and data['customer_id']:
            print("MMMMMMMMMMMMMMMMMMMMMMMMMMMmm")

  
            lines_list = []
            for check  in check_followups.filtered(lambda r: r.account_holder.id == data['customer_id']):
                operation_line = []
                operation_line = [check.state,check.Date,check.check_no,check.payment_id.check_date,check.payment_id.journal_id.name,check.amount]
                lines_list.append(operation_line)

           
            lines_dict = {}
            for rec in lines_list:

                if rec[0] in lines_dict:
                    lines_dict[rec[0]].append([rec[1],rec[2],rec[3],rec[4],rec[5]])

                else:

                    lines_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]


            return lines_dict


        if data['date_from'] and data['date_to'] and data['customer_id'] and data['state']:
            print("MMMMMMMMMMMMMMMMMMMMMMMMMMMmm")

            customers = data['customer_id']
            for rec in customers:
                custom_list = [] 
                customer = self.env['res.partner'].browse(rec)
                name = customer.name

            lines_list = []
            for check  in check_followups.filtered(lambda r: r.account_holder.id == data['customer_id'] and r.state == data['state']):
                custom_list.append({
                       'name': check.Date,
                       # 'date_order': order.date_order,
                       # 'date_planned': order.date_planned,
                       # 'product_id': line.product_id.name,
                       # 'product_qty': line.product_qty,
                       # 'product_uom': line.product_uom.name,
                       # 'price_unit': line.price_unit,
                  
                    })
                operation_line = []
                operation_line = [check.state,check.Date,check.check_no,check.payment_id.check_date,check.payment_id.journal_id.name,check.amount]
                lines_list.append(operation_line)

           
            # lines_dict = {}
            # for rec in lines_list:

            #     if rec[0] in lines_dict:
            #         lines_dict[rec[0]].append([rec[1],rec[2],rec[3],rec[4],rec[5]])

            #     else:

            #         lines_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]


            return lines_dict
    @api.model
    def _get_report_values(self, docids, data=None):
        data['records'] = self.env['check_followups.check_followups'].browse(data)
        docs = data['records']
        cheque_report = self.env['ir.actions.report']._get_report_from_name('zaway_account_custom.cheque_template')
        docargs = {

            'data': data,
            'docs': docs,
        }
        return {
            'doc_ids': self.ids,
            'doc_model': cheque_report.model,
            'docs': data,
            'get_info': self._get_header_info(data),
            'get_report': self._get_cheque(data),
        }
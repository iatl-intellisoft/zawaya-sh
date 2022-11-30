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
        customer_id = data['customer_id']
        state = data['state']

        return {
            'date_from': date_from,
            'date_to': date_to,
            'customer_id': customer_id,
            'state': state,
            # 'company_id': company_id,

        }

    def _get_cheque(self, data):

        if data['date_from'] > data['date_to']:
            raise UserError(_("You must enter a start date less than the end date."))


        check_followups = self.env['check_followups.check_followups'].search([
            ('Date', '>=', data['date_from']),
            ('Date', '<=',data['date_to'])])

# Not customers and not state
        if data['date_from'] and data['date_to'] and not data['customer_id'] and not data['state']:
            print("!!!!!!!!! Not customers and not stat::::::::::")
            customers = self.env['res.partner'].search([])
            lisy = []
            for rec in customers:
                custom_list = [] 
                customer = self.env['res.partner'].browse(rec)
                name = rec.name

                lines_list = []
                for check  in check_followups.filtered(lambda r: r.account_holder == rec):
                    operation_line = []
                    # get state
                    state = ''
                    if check.state == 'under_collection':
                        state = 'Under Collection'
                    if check.state == 'in_bank':
                        state = 'In Bank'
                    if check.state in ['rdc','rdv']:
                        state = 'Check Rejected'
                    if check.state in ['return_acc','return_acv']:
                        state = 'Return to Partner'
                    if check.state in ['donec','donev']:
                        state = 'Done'
                    if check.state == 'out_standing':
                        state = 'Out Standing'
                    if check.state == 'withdrawal':
                        state = 'Withdraw From Bank'
                    if check.state == 'cancel':
                        state = 'Cancel'
                    operation_line = [state,check.Date,check.check_no,check.payment_id.check_date,check.payment_id.journal_id.name,check.amount]
                    lines_list.append(operation_line)

           
                lines_dict = {}
                for rec in lines_list:

                    if rec[0] in lines_dict:
                        lines_dict[rec[0]].append([rec[1],rec[2],rec[3],rec[4],rec[5]])

                    else:

                        lines_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]
                if lines_dict:       
                    lisy.append({

                        'name': name,
                        'list': lines_dict,
                        })
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",lisy)

            return lisy

# customers and not state
        if data['date_from'] and data['date_to'] and data['customer_id'] and not data['state']:
            print("$################ customers and not state")
            lisy = []
            customers = data['customer_id']
            for rec in customers:
                custom_list = [] 
                customer = self.env['res.partner'].browse(rec)
                name = customer.name

                lines_list = []
                
                for check  in check_followups.filtered(lambda r: r.account_holder.id == rec):
                    # get state
                    state = ''
                    if check.state == 'under_collection':
                        state = 'Under Collection'
                    if check.state == 'in_bank':
                        state = 'In Bank'
                    if check.state in ['rdc','rdv']:
                        state = 'Check Rejected'
                    if check.state in ['return_acc','return_acv']:
                        state = 'Return to Partner'
                    if check.state in ['donec','donev']:
                        state = 'Done'
                    if check.state == 'out_standing':
                        state = 'Out Standing'
                    if check.state == 'withdrawal':
                        state = 'Withdraw From Bank'
                    if check.state == 'cancel':
                        state = 'Cancel'

                    operation_line = []
                    operation_line = [state,check.Date,check.check_no,check.payment_id.check_date,check.payment_id.journal_id.name,check.amount]
                    lines_list.append(operation_line)

                print("__________________________________line",lines_list)
                # print("__________________________________lineDi",lines_dict)
                lines_dict = {}
                for rec in lines_list:

                    if rec[0] in lines_dict:
                        lines_dict[rec[0]].append([rec[1],rec[2],rec[3],rec[4],rec[5]])

                    else:

                        lines_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]


                print("___222_______________________________lineDi",lines_dict)


                lisy.append({

                    'name': name,
                    'list': lines_dict,
                    })

            return lisy

# Not customers and state
        if data['date_from'] and data['date_to'] and not data['customer_id'] and data['state']:
            if data['state'] == 'reject':
                check_followups = self.env['check_followups.check_followups'].search([
                    ('Date', '>=', data['date_from']),
                    ('Date', '<=',data['date_to']),
                    ('state','in',['rdc','rdv'])])

            elif data['state'] == 'return':
                check_followups = self.env['check_followups.check_followups'].search([
                    ('Date', '>=', data['date_from']),
                    ('Date', '<=',data['date_to']),
                    ('state','in',['return_acc','return_acc'])])

            elif data['state'] == 'done':
                check_followups = self.env['check_followups.check_followups'].search([
                    ('Date', '>=', data['date_from']),
                    ('Date', '<=',data['date_to']),
                    ('state','in',['donec','donev'])])

            customers = self.env['res.partner'].search([])
            lisy = []
            for rec in customers:
                custom_list = []
                name = rec.name
                lines_list = []
                print("___________________________",rec)

                print("@################################333",check_followups)
                if data['state'] == 'return' or data['state'] == 'reject' or data['state'] == 'done':
                    followups = check_followups.filtered(lambda r: r.account_holder == rec)
                else:
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!else")
                    followups = check_followups.filtered(lambda r: r.account_holder == rec and r.state == data['state'])
                    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",data['state'],followups)
                

                print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVv",check_followups)
                for check  in followups:
                    # get state
                    state = ''
                    if check.state == 'under_collection':
                        state = 'Under Collection'
                    if check.state == 'in_bank':
                        state = 'In Bank'
                    if check.state in ['rdc','rdv']:
                        state = 'Check Rejected'
                    if check.state in ['return_acc','return_acv']:
                        state = 'Return to Partner'
                    if check.state in ['donec','donev']:
                        state = 'Done'
                    if check.state == 'out_standing':
                        state = 'Out Standing'
                    if check.state == 'withdrawal':
                        state = 'Withdraw From Bank'
                    if check.state == 'cancel':
                        state = 'Cancel'

                    operation_line = []
                    operation_line = [state,check.Date,check.check_no,check.payment_id.check_date,check.payment_id.journal_id.name,check.amount]
                    lines_list.append(operation_line)

           
                lines_dict = {}
                for rec in lines_list:

                    if rec[0] in lines_dict:
                        lines_dict[rec[0]].append([rec[1],rec[2],rec[3],rec[4],rec[5]])

                    else:

                        lines_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]
                if lines_dict:       
                    lisy.append({

                        'name': name,
                        'list': lines_dict,
                        })

            return lisy

# Customer and State
        if data['date_from'] and data['date_to'] and data['customer_id'] and data['state']:
            if data['state'] == 'reject':
                check_followups = self.env['check_followups.check_followups'].search([
                    ('Date', '>=', data['date_from']),
                    ('Date', '<=',data['date_to']),
                    ('state','in',['rdc','rdv'])])

            elif data['state'] == 'return':
                check_followups = self.env['check_followups.check_followups'].search([
                    ('Date', '>=', data['date_from']),
                    ('Date', '<=',data['date_to']),
                    ('state','in',['return_acc','return_acc'])])

            elif data['state'] == 'done':
                check_followups = self.env['check_followups.check_followups'].search([
                    ('Date', '>=', data['date_from']),
                    ('Date', '<=',data['date_to']),
                    ('state','in',['donec','donev'])])


            lisy = []
            customers = data['customer_id']
            for rec in customers:
                custom_list = [] 
                customer = self.env['res.partner'].browse(rec)
                name = customer.name

                lines_list = []
                if data['state'] == 'return' or data['state'] == 'reject' or data['state'] == 'done':
                    followups = check_followups.filtered(lambda r: r.account_holder.id == rec)
                else:
                    followups = check_followups.filtered(lambda r: r.account_holder.id == rec and r.state == data['state'])
                for check  in followups:
                    # get state
                    state = ''
                    if check.state == 'under_collection':
                        state = 'Under Collection'
                    if check.state == 'in_bank':
                        state = 'In Bank'
                    if check.state in ['rdc','rdv']:
                        state = 'Check Rejected'
                    if check.state in ['return_acc','return_acv']:
                        state = 'Return to Partner'
                    if check.state in ['donec','donev']:
                        state = 'Done'
                    if check.state == 'out_standing':
                        state = 'Out Standing'
                    if check.state == 'withdrawal':
                        state = 'Withdraw From Bank'
                    if check.state == 'cancel':
                        state = 'Cancel'

                    operation_line = []
                    operation_line = [state,check.Date,check.check_no,check.payment_id.check_date,check.payment_id.journal_id.name,check.amount]
                    lines_list.append(operation_line)

           
                lines_dict = {}
                for rec in lines_list:

                    if rec[0] in lines_dict:
                        lines_dict[rec[0]].append([rec[1],rec[2],rec[3],rec[4],rec[5]])

                    else:

                        lines_dict[rec[0]] = [[rec[1],rec[2],rec[3],rec[4],rec[5]]]

                if lines_dict:     
                    lisy.append({

                        'name': name,
                        'list': lines_dict,
                        })

            return lisy
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
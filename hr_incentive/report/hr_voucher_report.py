# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

import time
from datetime import date, datetime
from odoo import models, api ,_
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from num2words import num2words

class HrVoucherAbstract(models.AbstractModel):
    _inherit = 'report.hr_payroll_custom.voucher_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        result = []
        domain = []
        result_lines = {}
        moves = self.env['account.move'].browse(docids)
        incentives = self.env['hr.incentive'].search([('move_id','in',docids)])
        if incentives:
            domain = [('incentive_id','in',incentives.ids)]
            if moves[0].bank_id:
                domain.append(('bank_id','=',moves[0].bank_id.id))
            else:
                domain.append(('bank_id','=',False))
            incentive_ids = self.env['hr.incentive.line'].search(domain)
        else:
            return super(HrVoucherAbstract,self)._get_report_values(docids=docids, data=data)
        date,month = self._get_date(incentive_ids[0].date)
        for pay in incentive_ids:
            result_lines = {}
            result_lines['employee'] = pay.employee_id.name
            result_lines['acc_number'] = pay.employee_id.bank_account_id.acc_number
            result_lines['amount'] = round(pay.amount,2)
            result.append(result_lines)
        incentive_total = round(sum(incentive.amount for incentive in incentive_ids),2)
        incentive_total_text = incentive_ids[0].company_id.currency_id.with_context(lang='ar_001').amount_to_text(incentive_total)
        return {
           'docs' : self.env['account.move'].browse(docids),
           'result' : result,
           'total':incentive_total,
           'total_text':incentive_total_text,
           'date' : date,
           'month' : month}

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

class PayslipReport(models.AbstractModel):

    _name = 'report.hr_payroll_custom.payroll_report_template'

    

    @api.model
    def _get_report_values(self, docids,data=None):
        payslips = self.env['hr.payslip.run'].browse(docids)
        return { 'docs': self.env['hr.payslip.run'].browse(docids),
                 'fun':self._get_rule_total,

                }


    def _get_rule_total(self,rule,run):
        the_rule = sum(run.mapped('slip_ids').mapped('line_ids').filtered(lambda line: line.salary_rule_id.id == rule.id).mapped('total'))
        return the_rule




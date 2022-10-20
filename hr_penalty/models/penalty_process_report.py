# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PenaltyProcessReport(models.AbstractModel):
    _name = 'report.hr_penalty.report_penalty_document'
    _description = 'Penalty Process Report'

    def _get_penalty(self, employee_id):
        """
        A method to get penalty
        """
        self.hr_penalty()
        line = self.line_ids.filtered(lambda line: line.employee_id == employee_id)
        if line:
            return line[0].total
        else:
            return 0.0

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        A method to get penalty report
        """
        result = {}
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        line = self.env.get('employee_id')
        employee_id = self.env['hr.penalty'].browse(line)
        for rec in self.env['hr.penalty'].browse(employee_id):
            line.search([('employee_id', '=', employee_id)])
            return result

        return {
            'doc_ids': line,
            'doc_model': 'hr.penalty',
            'docs': employee_id,
            'data': data,
        }

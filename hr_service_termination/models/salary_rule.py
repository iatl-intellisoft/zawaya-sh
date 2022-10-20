# -*- coding: utf-8 -*-
###############################################################################
#
#    IATL-Intellisoft International Pvt. Ltd.
#    Copyright (C) 2021 Tech-Receptives(<http://www.iatl-intellisoft.com>).
#
###############################################################################

from odoo import models, fields, api

class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    use_type = fields.Selection(selection_add=[('termination','Termination')])

    def _satisfy_condition(self, localdict):
        #Desc TO DO
        self.ensure_one()
        if 'payslip' not in localdict:
            return super(SalaryRule, self)._satisfy_condition(localdict)
        if localdict['payslip'] and localdict['payslip'].type=='salary':
            if self.use_type == 'termination':
                return False
            else:
                return super(SalaryRule, self)._satisfy_condition(localdict)
        elif localdict['payslip'] and localdict['payslip'].type=='service_termination':
            if self.use_type == 'salary' or self.id not in localdict['payslip'].termination_id.reason_id.rule_ids.ids:
                return False
            else:
                return super(SalaryRule, self)._satisfy_condition(localdict)
        else:
            return super(SalaryRule, self)._satisfy_condition(localdict)


    

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=False)

class HrPayslip(models.Model):
    """"""
    _inherit = 'hr.payslip'

    over_time_ids = fields.One2many('hr.overtime', 'payslip_id', string='Over time')
    overtime_amount = fields.Float(string='overtime_amount', compute='_compute_overtime')

    @api.depends('over_time_ids')
    def _compute_overtime(self):
        """
        A method to compute total overtime amount.
        """
        amount = 0.0
        for record in self:
            record.overtime_amount = 0.0
            for over in record.over_time_ids:
                amount += over.total_amount
            record.overtime_amount = amount

    def get_overtime(self):
        """
        A method to get overtime lines in specific situation.
        """
        array = []
        for rec in self:
            rec.over_time_ids.write({'payslip_id': False})
            rec.over_time_ids = self.env['hr.overtime'].search(
                [('start_date', '>=', rec.date_from),
                 ('end_date', '<=', rec.date_to),
                 ('state', '=', 'approve'),
                 ('paid', '=', False), ('employee_id', '=', rec.employee_id.id),
                 ('company_overtime_type', '=', 'payroll')])
        return True


    def compute_sheet(self):
        """
        A compute_sheet inherited to compute overtime in payslip.
        """
        self.get_overtime()
        return super(HrPayslip, self.sudo()).compute_sheet()

    # @api.multi
    def action_payslip_done(self):
        """
        A action_payslip_done method inherited and change overtime to paid to make overtime done.
        """
        res = super(HrPayslip, self.sudo()).action_payslip_done()
        self.over_time_ids.write({'paid': True,'payslip_id':self.id})
        return res


class HrSalaryRule(models.Model):
    """"""
    _inherit = 'hr.salary.rule'

    use_type = fields.Selection(
        string=u'Use Type',
        selection_add=[('over_time', 'Over Time')])

    def _satisfy_condition(self, localdict):
        """"""
        res = super(HrSalaryRule, self)._satisfy_condition(localdict)
        contract = localdict['contract']
        if 'payslip' in localdict:
            if self.use_type == "over_time":
                amount = localdict['payslip'].overtime_amount
                if amount != 0.0:
                    return super(HrSalaryRule, self)._satisfy_condition(localdict)
                else:
                    return False
            else:
                return super(HrSalaryRule, self)._satisfy_condition(localdict)
        else:
            return super(HrSalaryRule, self)._satisfy_condition(localdict)

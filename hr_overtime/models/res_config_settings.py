from odoo import fields, models


class ResCompany(models.Model):
    """"""
    _inherit = 'res.company'

    working_day_rate = fields.Float('Working Days Rate', )
    weekend_rate = fields.Float('Weekends Rate ', )
    public_holiday_rate = fields.Float('Public Holidays Rates', )
    overtime_rule_id = fields.Many2one('hr.salary.rule', string='Rule Salary *',
                                        domain="[('use_type','=','over_time')]")

    overtime_template_id = fields.Many2one('mail.template', string='Overtime Template',
                                           domain="[('model','=','hr.overtime.batch')]")

    overtime_type = fields.Selection([('payroll', 'Through Payroll'),
                                      ('receipt', 'Through Receipt')], default='receipt')
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type', '=', 'purchase')])
    account_id = fields.Many2one('account.account', string='Account')
    overtime_partner_id = fields.Many2one('res.partner', string='Receipt Partner')


class ResConfigSettings(models.TransientModel):
    """"""
    _inherit = 'res.config.settings'

    working_day_rate = fields.Float(related='company_id.working_day_rate', string="Working Days Rate", readonly=False)
    weekend_rate = fields.Float(related='company_id.weekend_rate', string="Weekends Rate", readonly=False)
    public_holiday_rate = fields.Float(related='company_id.public_holiday_rate', string="Public Holidays Rates",
                                       readonly=False)
    overtime_rule_id = fields.Many2one('hr.salary.rule', string='Rule Salary *', related='company_id.overtime_rule_id',
                                       readonly=False)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)

    overtime_template_id = fields.Many2one('mail.template', string='Overtime Template',
                                           related='company_id.overtime_template_id', readonly=False)

    overtime_type = fields.Selection([('payroll', 'Through Payroll'),
                                      ('receipt', 'Through Receipt')],
                                     related='company_id.overtime_type', readonly=False)
    journal_id = fields.Many2one('account.journal', domain=[('type', '=', 'purchase')],
                                 related='company_id.journal_id', string='Journal', required=False, readonly=False)
    account_id = fields.Many2one('account.account', related='company_id.account_id', string='Account', readonly=False)
    overtime_partner_id = fields.Many2one('res.partner', related='company_id.overtime_partner_id', string='Partner', readonly=False)
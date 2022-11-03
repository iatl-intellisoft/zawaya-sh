from datetime import datetime
from dateutil import relativedelta
import time

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.osv import osv
import babel


class AccountGroup(models.Model):
    _inherit = 'account.group'

    code = fields.Char('Code')
    parent_id = fields.Many2one('account.group', index=True, ondelete='cascade', readonly=False)

    def _adapt_parent_account_group(self):
        """Ensure consistency of the hierarchy of account groups.

        Find and set the most specific parent for each group.
        The most specific is the one with the longest prefixes and with the starting
        prefix being smaller than the child prefixes and the ending prefix being greater.
        """
        if self.code_prefix_start:
            if not self:
                return
            self.env['account.group'].flush()
            query = """
                UPDATE account_group agroup SET parent_id = (
                    SELECT parent.id FROM account_group parent
                    WHERE char_length(parent.code_prefix_start) < char_length(agroup.code_prefix_start)
                    AND parent.code_prefix_start <= LEFT(agroup.code_prefix_start, char_length(parent.code_prefix_start))
                    AND parent.code_prefix_end >= LEFT(agroup.code_prefix_end, char_length(parent.code_prefix_end))
                    AND parent.id != agroup.id
                    AND parent.company_id = %(company_id)s
                    ORDER BY char_length(parent.code_prefix_start) DESC LIMIT 1
                ) WHERE agroup.company_id = %(company_id)s;
            """
            self.env.cr.execute(query, {'company_id': self.company_id.id})
            self.env['account.group'].invalidate_cache(fnames=['parent_id'])
            self.env['account.group'].search([('company_id', '=', self.company_id.id)])._parent_store_update()



    def _adapt_accounts_for_account_groups(self, account_ids=None):
        print('hi7')
        """Ensure consistency between accounts and account groups.

        Find and set the most specific group matching the code of the account.
        The most specific is the one with the longest prefixes and with the starting
        prefix being smaller than the account code and the ending prefix being greater.
        """
        if not self and not account_ids:
            return
        self.env['account.group'].flush()
        self.env['account.account'].flush()
        if not self.code:
            query = """
                UPDATE account_account account SET group_id = (
                    SELECT agroup.id FROM account_group agroup
                    WHERE agroup.code_prefix_start <= LEFT(account.code, char_length(agroup.code_prefix_start))
                    AND agroup.code_prefix_end >= LEFT(account.code, char_length(agroup.code_prefix_end))
                    AND agroup.company_id = account.company_id
                    ORDER BY char_length(agroup.code_prefix_start) DESC LIMIT 1
                ) WHERE account.company_id in %(company_ids)s {where_account};
            """.format(
                where_account=account_ids and 'AND account.id IN %(account_ids)s' or ''
            )
            self.env.cr.execute(query, {'company_ids': tuple((self.company_id or account_ids.company_id).ids), 'account_ids': account_ids and tuple(account_ids.ids)})
            self.env['account.account'].invalidate_cache(fnames=['group_id'])

    # To Generate Account Code by Default
    @api.onchange('parent_id')
    def _onchange_code(self):
        if self.parent_id:
            group_code = str(self.parent_id.code)
            no = len(self.search([('parent_id', '=', self.parent_id.id)]))
            self.code = group_code + '0' + str(no + 1)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    group_id = fields.Many2one('account.group', readonly=False ,store=True , compute=False)

    # To Generate Account Code by Default
    @api.onchange('group_id')
    def _onchange_account_code(self):
        if self.group_id:
            group_code = str(self.group_id.code)
            no = len(self.search([('group_id', '=', self.group_id.id), ('deprecated', '=', False)],order= 'id desc'))
            next_no = self.search([('group_id', '=', self.group_id.id), ('deprecated', '=', False)],order= 'code desc',limit=1)
            if no >= 1:
                x = int(next_no.code) + 1
            else:
                str_code= str(self.group_id.code )+ str('01')
                x = int(str_code)
            print(no,next_no,x)
            self.code = str(x)

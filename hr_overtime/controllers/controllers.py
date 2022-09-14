# -*- coding: utf-8 -*-
from odoo import http

# class HrOvertime(http.Controller):
#     @http.route('/hr_overtime/hr_overtime/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_overtime/hr_overtime/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_overtime.listing', {
#             'root': '/hr_overtime/hr_overtime',
#             'objects': http.request.env['hr_overtime.hr_overtime'].search([]),
#         })

#     @http.route('/hr_overtime/hr_overtime/objects/<model("hr_overtime.hr_overtime"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_overtime.object', {
#             'object': obj
#         })
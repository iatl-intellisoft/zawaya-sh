# -*- coding: utf-8 -*-
# from odoo import http


# class FixedBomLine(http.Controller):
#     @http.route('/fixed_bom_line/fixed_bom_line/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fixed_bom_line/fixed_bom_line/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fixed_bom_line.listing', {
#             'root': '/fixed_bom_line/fixed_bom_line',
#             'objects': http.request.env['fixed_bom_line.fixed_bom_line'].search([]),
#         })

#     @http.route('/fixed_bom_line/fixed_bom_line/objects/<model("fixed_bom_line.fixed_bom_line"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fixed_bom_line.object', {
#             'object': obj
#         })

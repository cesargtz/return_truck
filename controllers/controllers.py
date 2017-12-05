# -*- coding: utf-8 -*-
from odoo import http

# class ReturnTruck(http.Controller):
#     @http.route('/return_truck/return_truck/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/return_truck/return_truck/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('return_truck.listing', {
#             'root': '/return_truck/return_truck',
#             'objects': http.request.env['return_truck.return_truck'].search([]),
#         })

#     @http.route('/return_truck/return_truck/objects/<model("return_truck.return_truck"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('return_truck.object', {
#             'object': obj
#         })
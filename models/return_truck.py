# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

class ReturnTruck(models.Model):
    _inherit = ['truck', 'vehicle.reception', 'mail.thread']
    _name = 'return.truck'

    state = fields.Selection([
        ('validation', 'Validación'),
        ('weight_input', 'Peso de entrada'),
        ('analysis', 'Analisis'),
        ('weight_output', 'Peso de salida'),
        ('done', 'Hecho'),
    ], default='validation')

    location_dest_id = fields.Many2one('stock.location', 'Ubicación Destino')
    tons_validate = fields.Float("Toneladas a validar",required=True)
    tons_free = fields.Float(readonly=True, digits=(12,3))

    @api.constrains('tons_validate')
    def _check_tons(self):
        avalible = self.calculate_total_tons(self.contract_id.id)
        if self.tons_validate > (avalible - self.tons_validate):
            raise exceptions.ValidationError("No tienes las suficientes toneladas para sacar del almacén.")

    @api.multi
    def calculate_total_tons(self, contract_id,):
        tons_available = self.env['purchase.order']._get_tons_avalible(contract_id)
        tons_priced = sum(tons.pinup_tons for tons in self.env['pinup.price.purchase'].search([('purchase_order_id','=', contract_id),('state','=','close')]))
        tons_return = sum(ta.tons_validate for ta in self.env['return.truck'].search([('contract_id','=', contract_id)]))
        return tons_available - (tons_priced + tons_return)

    @api.onchange('contract_id')
    def _compute_free(self):
        self.tons_free  = float(self.calculate_total_tons(self.contract_id.id))
        # self.tons_free = float(free) - float(self.tons_validate)

    @api.multi
    def write(self, vals, recursive=None):
        if not recursive:
            if self.state == 'weight_input':
                self.write({'state': 'analysis'}, 'r')
            elif self.state == 'analysis':
                self.write({'state': 'weight_output'}, 'r')
            elif self.state == 'weight_output':
                self.write({'state': 'done'}, 'r')
        res = super(ReturnTruck, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        vals['state'] = 'weight_input'
        res = super(ReturnTruck, self).create(vals)
        return res

    @api.multi
    def copy(self):
        raise exceptions.ValidationError('No es posible duplicar.')

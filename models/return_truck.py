# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import requests
import json
import datetime
import pytz

class ReturnTruck(models.Model):
    _inherit = ['truck', 'vehicle.reception', 'mail.thread']
    _name = 'return.truck'

    name = fields.Char('Return Truck Reference', required=True, select=True, copy=False, default=lambda self: self.env[
                       'ir.sequence'].next_by_code('reg_return_truck'), help="Unique number of the return truck")

    state = fields.Selection([
        ('validation', 'Validación'),
        ('weight_input', 'Peso de entrada'),
        ('analysis', 'Analisis'),
        ('weight_output', 'Peso de salida'),
        ('done', 'Hecho'),
    ], default='validation')

    stock_type = fields.Many2one('stock.picking.type', 'tipo de albaran')
    location_dest_id = fields.Many2one('stock.location', 'Ubicación Destino')
    tons_validate = fields.Float("Toneladas a validar", required=True)
    tons_free = fields.Float(readonly=True, digits=(12, 3))

    @api.constrains('tons_validate')
    def _check_tons(self):
        avalible = self.calculate_total_tons(self.contract_id.id)
        if self.tons_validate > (avalible ):
            raise exceptions.ValidationError(
                "No tienes las suficientes toneladas para sacar del almacén.")

    @api.multi
    def calculate_total_tons(self, contract_id,):
        tons_available = self.env[
            'purchase.order']._get_tons_avalible(contract_id)
        tons_priced = sum(tons.pinup_tons for tons in self.env['pinup.price.purchase'].search(
            [('purchase_order_id', '=', contract_id), ('state', '=', 'close')]))
        return tons_available - tons_priced

    @api.onchange('contract_id')
    def _compute_free(self):
        self.tons_free = float(self.calculate_total_tons(self.contract_id.id))
        self.date = None

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

    @api.one
    def weight_input(self):
        url = 'http://nvryecora.ddns.net:8081'
        response = requests.get(url)
        json_data = json.loads(response.text)
        if json_data['id'] == self.name[-3:]:
            self.output_kilos = float(json_data['peso_entrada'])
            self.write({'state': 'weight_output'}, 'r')
        else:
            raise exceptions.ValidationError('Id de la bascula no coincide')

    @api.one
    def weight_output(self):
        url = 'http://nvryecora.ddns.net:8081'
        response = requests.get(url)
        json_data = json.loads(response.text)
        if json_data['id'] == self.name[-3:]:
            if float(json_data['peso_salida']) > 1:
                self.input_kilos = float(json_data['peso_salida'])
                self.write({'state': 'done'}, 'r')
            else:
                raise exceptions.ValidationError('Revisar el id de bascula')
        else:
            raise exceptions.ValidationError('Id de la bascula no coincide')

    @api.onchange('raw_kilos')
    def _onchange_rawkilos(self):
        if (self.raw_kilos / 1000) > self.tons_validate:
            return {
                'warning': {
                    'title': _("TONELADAS EXCEDIDAS"),
                    'message': _("Se validarón %s toneladas y se van a transerir %s toneladas, estas seguro ?" % (self.tons_validate, self.raw_kilos/1000)),
                },
            }

    @api.multi
    def action_return_product(self):
        grupo_id = self.env['procurement.group'].search([('name','=',self.contract_id.name)], limit=1)
        print("***********")
        print(grupo_id.id)
        move = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'group_id': grupo_id.id,
            'min_date': self.date,
            'origin': self.contract_id.name,
            'owner_id': self.owner_id.id,
            'picking_type_id': 3,
            })


        self.env['stock.pack.operation'].create({
            'product_id': self.product_id.id,
            'product_qty': self.raw_kilos / 1000,
            'ordered_qty': self.raw_kilos / 1000,
            'qty_done': self.raw_kilos / 1000,
            'product_uom_id': self.product_id.product_tmpl_id.uom_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'owner_id': self.owner_id.id,
            'picking_id': move.id,
            })

        self.env['stock.move'].create({
            'product_id': self.product_id.id,
            'origin': self.contract_id.name,
            'price_unit': self.product_id.product_tmpl_id.standard_price,
            'partner_id': self.partner_id.id,
            'product_uom_qty': self.raw_kilos / 1000,
            'product_uom': self.product_id.product_tmpl_id.uom_id.id,
            'name': "Salida de exedente",
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'picking_type_id': 4,
            'picking_id': move.id,
            'group_id': grupo_id.id,
            })

        move.action_confirm()
        move.action_done()
        self.stock_picking_id = self.env['stock.picking'].search(
            [('state', 'in', ['done'])], order='date desc', limit=1)

# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    service_count = fields.Integer(string="Service History", compute='_compute_service_count')
    status = fields.Selection(
        [('nonservice', 'Non Service'), ('service', 'Service')], default="nonservice",
        string='Status')

    def _compute_service_count(self):
        for rec in self:
            service_count = self.env['vehicle.repair'].search_count([('customer_id', '=', rec.id)])
            rec.service_count = service_count

    def show_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service Transfer',
            'res_model': 'vehicle.repair',
            'domain': [('customer_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def open_service_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service',
            'view_mode': 'form',
            'res_model': 'vehicle.repair',
            'view_id': self.env['res.partner'],
            'context': {
                'default_customer_id': self.id,
                'default_phone': self.phone,
            }
        }

    def action_archive(self):
        res = super().action_archive()
        repair = self.env['vehicle.repair'].search([('customer_id', 'in', self.ids)])
        repair.write({'active': False})
        return res

    def action_unarchive(self):
        res = super().action_unarchive()
        repair = self.env['vehicle.repair'].sudo().search([('customer_id', 'in', self.ids), ('active', '=', False)])
        repair.write({'active': True})
        return res

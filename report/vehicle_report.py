# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RepairInformation(models.AbstractModel):
    _name = "report.vehicle_repair.report_vehiclerepair"
    _description = " Repair Information"

    @api.model
    def _get_report_values(self, docids, data=None):
        print('datatta', data['date'].get('group_by') == 'service_type')
        if data['date'].get('group_by') == 'service_type':
            data['service_types'] = ['paid', 'free']
        if data['date'].get('group_by') == 'vehicle_type_id':
            datass = self.env['fleet.vehicle.model.category'].sudo().search([])
            data['vehicle_types'] = datass.mapped('name')

        returns = {'doc_ids': docids,
                   'doc_model': 'vehicle.repair',
                   'data': data,
                   }
        return returns

from odoo import http
from odoo.http import request
from datetime import datetime


class WebsiteForm(http.Controller):
    @http.route(['/repairs'], type='http', auth='user', website=True)
    def repair(self):
        partners = request.env['res.partner'].sudo().search([])
        advisor = request.env['res.users'].sudo().search([])
        vehicle_model = request.env['fleet.vehicle.model'].sudo().search([])
        data = {'partners': partners, 'advisor': advisor, 'vehicle_model': vehicle_model}
        return request.render("vehicle_repair.repair_form", data)

    @http.route(['/create_repairs'], type='http', auth='user', website=True)
    def repair_creation(self, **kw):
        a = int(kw.get('customer_id', False))
        b = int(kw.get('vehicle_model_id', False))
        c = kw.get('vehicle_number', False)
        existing_record = request.env['vehicle.repair'].sudo().search([
            ('customer_id', '=', a),
            ('vehicle_model_id', '=', b),
            ('vehicle_number', '=', c),
            ('start_date', '=', datetime.today()),
        ])
        if existing_record:
            new_record = request.env['vehicle.repair'].sudo().create(kw)
            return request.render("vehicle_repair.thanks_form")
        else:
            return request.render("vehicle_repair.duplicate_error_form")

    @http.route(['/customer'], type='http', auth='user', website=True)
    def customer(self):
        return request.render("vehicle_repair.customer_form")

    @http.route(['/create_customer'], type='http', auth='user', website=True)
    def create_customer(self, **kw):
        new_customer_data = {
            'name': kw.get('name'),
            'email': kw.get('email'),
        }
        request.env['res.partner'].sudo().create(new_customer_data)
        return request.render("vehicle_repair.thanks_form")

    @http.route(['/latest_record'], type='json', auth='user', website=True)
    def snippet_record(self):
        new_record = request.env['vehicle.repair'].sudo().search_read([], order='create_date desc')
        record_list = [new_record[i:i + 4] for i in range(0, len(new_record), 4)]
        return record_list

    @http.route(['/details/<int:data_id>'], type="http", auth="public", website=True)
    def repair_details(self, data_id):
        details = request.env['vehicle.repair'].browse(data_id)
        values = {
            'details': details
        }
        return request.render('vehicle_repair.repair_details', values)

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import datetime
from odoo.exceptions import UserError
import io
import json
import xlsxwriter
from odoo import models
from odoo.tools import date_utils


class RepairWizard(models.TransientModel):
    _name = "repair.wizard"
    _description = " Repair Report"

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date", default=datetime.date.today())
    customer_ids = fields.Many2many('res.partner', string="Customer")
    service_advisor_ids = fields.Many2many('res.users', string="Service Advisor")
    service_type = fields.Selection([('free', 'Free'), ('paid', 'Paid')], string="Service Type", default="free")
    vehicle_type_id = fields.Many2one('fleet.vehicle.model.category', string="Vehicle Type",
                                      ondelete='set null')
    group_by = fields.Selection([('service_type', 'Service Type'), ('vehicle_type_id', 'Vehicle Type')],
                                string="Group By", default="service_type", required=True)

    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise UserError(_("Invalid date as start date should be less than end  date"))

    def get_query(self):
        query = """select
                fl.name as fleet,v.vehicle_number,pr.name,p
                .name as user_name,v.start_date,v.due_date,v.service_type,fv.name as vehicle,
                                v.state,v.estimated_amount,v.total_cost from vehicle_repair as v
                                left join fleet_vehicle_model as fl on fl.id = v.vehicle_model_id
                                left join fleet_vehicle_model_category as fv on fv.id = v.vehicle_type_id
                                left join res_partner as pr on pr.id = v.customer_id
                                left join res_users as ur on ur.id = v.service_advisor_id
                                left join res_partner as p on p.id = ur.partner_id
                                WHERE 1=1
                                """

        params = ()

        if self.group_by == 'service_type':
            query += " AND service_type IN %s"
            params += (tuple(['free', 'paid']),)
        elif self.group_by == 'vehicle_type_id':
            query += " AND vehicle_type_id IS NOT NULL"

        if self.start_date:
            query += " AND start_date BETWEEN %s AND %s"
            params += (self.start_date, self.end_date)

        if self.customer_ids:
            query += " AND customer_id IN %s"
            params += (tuple(self.customer_ids.ids),)

        if self.service_advisor_ids:
            query += " AND service_advisor_id IN %s"
            params += (tuple(self.service_advisor_ids.ids),)

        self.env.cr.execute(query, params)

    def generate_report(self):
        self.get_query()
        # print(res)
        report = self.env.cr.dictfetchall()
        count = len(self.customer_ids)
        adv_count = len(self.service_advisor_ids)
        data = {'date': self.read()[0], 'report': report, 'count': count, 'adv_count': adv_count,
                'group_by': self.group_by}
        print(data)
        return self.env.ref('vehicle_repair.action_vehicle_repair_report').report_action(self, data)

    def generate_xlsx_report(self):
        # self.get_query()
        report = self.env.cr.dictfetchall()
        count = len(self.customer_ids)
        adv_count = len(self.service_advisor_ids)
        data = {'date': self.read()[0], 'report': report, 'count': count, 'adv_count': adv_count,
                'group_by': self.group_by}
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'repair.wizard',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Repair Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column('B:L', 18)
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})

        if data['count'] == 1 and data['report']:
            customer_data = data['date'].get('customer_ids')
            if customer_data and isinstance(customer_data, list) and len(customer_data) > 0:
                sheet.merge_range('B4:C4', data['report'][0]['name'], cell_format)
        if data['adv_count'] == 1 and data['report']:
            adv_data = data['date'].get('service_advisor_ids')
            if adv_data and isinstance(adv_data, list) and len(adv_data) > 0:
                sheet.merge_range('B5:C5', data['report'][0]['user_name'], cell_format)
        if data['group_by'] == 'service_type':
            sheet.write('E6', 'Service Type', cell_format)

            if data['date'].get('group_by') == 'service_type':
                data['service_types'] = ['paid', 'free']
            i = 6
            sheet.merge_range('B2:I3', 'REPAIR REPORT', head)
            for rec in data['service_types']:
                sheet.write(f'B{i}', 'Vehicle Model', cell_format)
                sheet.write(f'C{i}', 'Vehicle Number', cell_format)
                if data.get('count') < 1:
                    sheet.write(f'D{i}', 'Customer', cell_format)
                if data.get('adv_count') < 1:
                    sheet.write(f'E{i}', 'Service Advisors', cell_format)
                    sheet.write(f'F{i}', 'Start Date', cell_format)
                    sheet.write(f'G{i}', 'End Date', cell_format)
                    sheet.write(f'H{i}', 'State', cell_format)
                    sheet.write(f'I{i}', 'Estimate Amount', cell_format)
                    sheet.write(f'J{i}', 'Total Amount', cell_format)
                    sheet.write(f'K{i}', 'Vehicle Type', cell_format)
                else:
                    sheet.write(f'D{i}', 'Start Date', cell_format)
                    sheet.write(f'E{i}', 'End Date', cell_format)
                    sheet.write(f'F{i}', 'State', cell_format)
                    sheet.write(f'G{i}', 'Estimate Amount', cell_format)
                    sheet.write(f'H{i}', 'Total Amount', cell_format)
                    sheet.write(f'I{i}', 'Vehicle Type', cell_format)

                j = i + 2
                for vehicle in (data['report']):
                    if rec == vehicle['service_type']:
                        B7 = i + 1
                        sheet.write(f'B{j}', vehicle['fleet'], cell_format)
                        sheet.write(f'C{j}', vehicle['vehicle_number'], cell_format)
                        if data.get('count') < 1:
                            sheet.write(f'D{j}', vehicle['name'], cell_format)
                        if data.get('adv_count') < 1:
                            sheet.write(f'E{j}', vehicle['user_name'], cell_format)
                            sheet.write(f'F{j}', vehicle['start_date'], cell_format)
                            sheet.write(f'G{j}', vehicle['due_date'], cell_format)
                            sheet.write(f'H{j}', vehicle['state'], cell_format)
                            sheet.write(f'I{j}', vehicle['estimated_amount'], cell_format)
                            sheet.write(f'J{j}', vehicle['total_cost'], cell_format)
                            sheet.write(f'B{B7}', vehicle['service_type'], cell_format)
                            sheet.write(f'K{j}', vehicle['vehicle'], cell_format)
                            j += 1

                        else:
                            sheet.write(f'D{j}', vehicle['start_date'], cell_format)
                            sheet.write(f'E{j}', vehicle['due_date'], cell_format)
                            sheet.write(f'F{j}', vehicle['state'], cell_format)
                            sheet.write(f'G{j}', vehicle['estimated_amount'], cell_format)
                            sheet.write(f'H{j}', vehicle['total_cost'], cell_format)
                            sheet.write(f'I{j}', vehicle['vehicle'], cell_format)
                            j += 1
                i = j + 2

        else:
            if data['group_by'] == 'vehicle_type_id':
                sheet.write('E6', 'Vehicle Type', cell_format)
                if data['date'].get('group_by') == 'vehicle_type_id':
                    datass = self.env['fleet.vehicle.model.category'].sudo().search([])
                    data['vehicle_types'] = datass.mapped('name')
                    i = 6
                    sheet.merge_range('B2:I3', 'REPAIR REPORT', head)

                    for rec in data['vehicle_types']:
                        if len(list(filter(lambda x: x['vehicle'] == rec, data['report']))):
                            sheet.write(f'B{i}', 'Vehicle Model', cell_format)
                            sheet.write(f'C{i}', 'Vehicle Number', cell_format)
                            if data.get('count') < 1:
                                sheet.write(f'D{i}', 'Customer', cell_format)
                            if data.get('adv_count') < 1:
                                sheet.write(f'E{i}', 'Service Advisors', cell_format)
                                sheet.write(f'F{i}', 'Start Date', cell_format)
                                sheet.write(f'G{i}', 'End Date', cell_format)
                                sheet.write(f'H{i}', 'State', cell_format)
                                sheet.write(f'I{i}', 'Estimate Amount', cell_format)
                                sheet.write(f'J{i}', 'Total Amount', cell_format)
                                sheet.write(f'K{i}', 'Service Type', cell_format)
                            else:
                                sheet.write(f'D{i}', 'Start Date', cell_format)
                                sheet.write(f'E{i}', 'End Date', cell_format)
                                sheet.write(f'F{i}', 'State', cell_format)
                                sheet.write(f'G{i}', 'Estimate Amount', cell_format)
                                sheet.write(f'H{i}', 'Total Amount', cell_format)
                                sheet.write(f'I{i}', 'Service Type', cell_format)

                            j = i + 2

                            for vehicle in (data['report']):
                                if rec == vehicle['vehicle']:
                                    B7 = i + 1
                                    sheet.write(f'B{j}', vehicle['fleet'], cell_format)
                                    sheet.write(f'C{j}', vehicle['vehicle_number'], cell_format)
                                    if data.get('count') < 1:
                                        sheet.write(f'D{j}', vehicle['name'], cell_format)
                                    if data.get('adv_count') < 1:
                                        sheet.write(f'E{j}', vehicle['user_name'], cell_format)
                                        sheet.write(f'F{j}', vehicle['start_date'], cell_format)
                                        sheet.write(f'G{j}', vehicle['due_date'], cell_format)
                                        sheet.write(f'H{j}', vehicle['state'], cell_format)
                                        sheet.write(f'I{j}', vehicle['estimated_amount'], cell_format)
                                        sheet.write(f'J{j}', vehicle['total_cost'], cell_format)
                                        sheet.write(f'K{j}', vehicle['service_type'], cell_format)
                                        sheet.write(f'B{B7}', vehicle['vehicle'], cell_format)
                                        j += 1

                                    else:
                                        sheet.write(f'D{j}', vehicle['start_date'], cell_format)
                                        sheet.write(f'E{j}', vehicle['due_date'], cell_format)
                                        sheet.write(f'F{j}', vehicle['state'], cell_format)
                                        sheet.write(f'G{j}', vehicle['estimated_amount'], cell_format)
                                        sheet.write(f'H{j}', vehicle['total_cost'], cell_format)
                                        sheet.write(f'I{j}', vehicle['service_type'], cell_format)
                                        j += 1
                            i = j + 2
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

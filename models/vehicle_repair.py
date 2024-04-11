# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from datetime import datetime
from datetime import timedelta, date
from odoo.exceptions import ValidationError


class VehicleRepair(models.Model):
    _name = "vehicle.repair"
    _description = "Vehicle Repair Management"
    _inherit = 'mail.thread'
    _rec_name = "reference_no"
    _order = 'id desc'

    @api.model
    def cancel_state(self):
        print("mmmm")
        service_record = (self.env['vehicle.repair'].
                          search([('state', '=', 'cancelled')]))
        datee = date.today() - timedelta(days=30)
        for rec in service_record:
            if rec.start_date and rec.start_date < (date.today() - timedelta(days=30)):
                service_record.write({'active': False})
                return rec

    @api.model
    def service_automation(self):
        self.customer_id.write({'status': 'service'})

    customer_id = fields.Many2one('res.partner', required=True, string="Customer",
                                  default=lambda self: _('New'))
    reference_no = fields.Char(string='Order Reference', required=True,
                               readonly=True, default=lambda self: _('New'))
    service_advisor_id = fields.Many2one('res.users', string="Service Advisor")
    vehicle_type_id = fields.Many2one('fleet.vehicle.model.category', string="Vehicle Type",
                                      ondelete='set null')
    vehicle_model_id = fields.Many2one('fleet.vehicle.model', required=True, string="Vehicle Model",
                                       domain="[('category_id', '=', vehicle_type_id)]")
    vehicle_number = fields.Char(string="Vehicle Number", required=True, copy=False)
    image = fields.Image(string="Image")
    mobile_no = fields.Char(string="Mobile", related='customer_id.phone', readonly=False)
    active = fields.Boolean(active=True, default=True, string="Active")
    start_date = fields.Date(string="Start Date", default=datetime.today())
    duration_days = fields.Integer(string="Duration")
    due_date = fields.Date(string='Estimated Delivery Date', compute='_compute_due_date', store=True)
    delivery_date = fields.Date(string="Delivery Date", readonly=True)
    next_date = fields.Date(string="Next Date", compute='_compute_next_date')
    today_date = fields.Date(string="Next Date", compute='_compute_today_date')
    service_type = fields.Selection([('free', 'Free'), ('paid', 'Paid')], string="Service Type", default="free",
                                    required=True)
    estimated_amount = fields.Monetary(string="Estimated Amount")
    customer_complaint = fields.Html(string="Customer Complaint")
    state = fields.Selection(
        [('draft', 'Draft'), ('inprogress', 'In progress'), ('readyfordelivery', 'Ready for Delivery'),
         ('done', 'Done'), ('cancelled', 'Cancelled')], default="draft",
        string='State', tracking=True)
    tags_ids = fields.Many2many('repair.tag', string="Tags")
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    labour_cost_ids = fields.One2many('labour.cost', 'vehicles_type_id', string="Cost")
    consumed_parts_ids = fields.One2many('consumed.parts',
                                         'vehicles_type_id', string="Consumed Parts")
    total_labour_cost = fields.Monetary(string="Total Labour Cost", compute='_compute_total_labour_cost',
                                        store=True)
    total_part_cost = fields.Monetary(string="Total Part Cost", compute='_compute_total_part_cost',
                                      store=True)

    total_cost = fields.Monetary(string="Total Cost", compute='_compute_total_cost', store=True)
    # invoice_count = fields.Integer(string="Invoice", compute='_compute_invoice_count')
    invoice_id = fields.Many2one('account.move', string="Invoice")
    invoice_created = fields.Boolean(string='Invoice Created', default=False)

    @api.depends("start_date")
    def _compute_next_date(self):
        self.next_date = datetime.today() + timedelta(days=1)

    @api.depends("start_date")
    def _compute_today_date(self):
        self.today_date = datetime.today() + timedelta(days=0)

    def create_invoice(self):
        labour_costs = self.labour_cost_ids.filtered(lambda x: x.hour_spend > 0)
        consumed_parts = self.consumed_parts_ids.filtered(lambda x: x.quantity > 0)

        invoice_data = {
            'partner_id': self.customer_id.id,
            'invoice_line_ids': [],
            'move_type': 'out_invoice',
        }

        for labour_cost in labour_costs:
            invoice_data['invoice_line_ids'].append((0, 0, {
                'name': labour_cost.labour_id.name,
                'product_id': self.env.ref("vehicle_repair.service_sample_product").id,
                'quantity': labour_cost.hour_spend,
                'price_unit': labour_cost.hourly_cost,
            }))

        for consumed_part in consumed_parts:
            invoice_data['invoice_line_ids'].append((0, 0, {
                'product_id': consumed_part.product_id.id,
                'quantity': consumed_part.quantity,
                'price_unit': consumed_part.unit_price,
            }))

        unpaid_invoice = self.env['account.move'].search([
            ('partner_id', '=', self.customer_id.id),
            ('state', '=', 'draft'),
        ])

        if unpaid_invoice:
            unpaid_invoice[0].write({'invoice_line_ids': [rec for rec in invoice_data['invoice_line_ids'] if
                                                          invoice_data['invoice_line_ids']]})
            self.invoice_id = unpaid_invoice[0].id
            return {
                'name': "Invoice Created",
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'view_type': 'form',
                'res_model': 'account.move',
                'res_id': self.invoice_id.id,
                'type': 'ir.actions.act_window',
            }
        else:
            invoice = self.env['account.move'].create(invoice_data)
            self.invoice_id = invoice.id
            self.write({
                'invoice_created': True
            })
            return {
                'name': "Invoice Created",
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'view_type': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'type': 'ir.actions.act_window',
            }

    def action_show_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    is_invoice_paid = fields.Boolean(string="Invoice Paid", compute="_compute_is_invoice_paid", store=True)
    ribbon_color = fields.Char(string="Ribbon Color", compute="_compute_ribbon_color", store=True)

    @api.depends('invoice_id.payment_state')
    def _compute_is_invoice_paid(self):
        for repair in self:
            repair.is_invoice_paid = repair.invoice_id.payment_state == 'paid'

    @api.depends('is_invoice_paid')
    def _compute_ribbon_color(self):
        for repair in self:
            repair.ribbon_color = 'green' if repair.is_invoice_paid else 'red'

    @api.depends('total_labour_cost', 'total_part_cost')
    def _compute_total_cost(self):
        for repair_record in self:
            repair_record.total_cost = repair_record.total_labour_cost + repair_record.total_part_cost

    @api.depends('labour_cost_ids.sub_total')
    def _compute_total_labour_cost(self):
        for repair_record in self:
            repair_record.total_labour_cost = sum(lc.sub_total for lc in repair_record.labour_cost_ids)

    @api.depends('consumed_parts_ids.subtotal')
    def _compute_total_part_cost(self):
        for repair_record in self:
            repair_record.total_part_cost = sum(pc.subtotal for pc in repair_record.consumed_parts_ids)

    def action_confirm(self):
        self.state = "inprogress"

    def action_ready_for_delivery(self):
        self.state = "readyfordelivery"
        template = self.env.ref('vehicle_repair.service_email_template')
        for rec in self:
            template.send_mail(rec.id, force_send=True)

    def action_create_invoice(self):
        self.state = "inprogress"

    def action_draft(self):
        self.state = "draft"

    def action_cancel(self):
        self.state = "cancelled"

    @api.onchange('state')
    def change_state(self):
        if self.state == 'done':
            self.delivery_date = datetime.now().date()

    def action_done(self):
        self.state = "done"
        self.write({
            'state': 'done',
            'delivery_date': datetime.now().date()
        })
        return True

    @api.model
    def create(self, vals):
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'vehicle.repair') or _('New')
        res = super(VehicleRepair, self).create(vals)
        return res

    @api.depends('start_date', 'duration_days')
    def _compute_due_date(self):
        for record in self:
            if record.start_date and record.duration_days:
                record.due_date = record.start_date + timedelta(days=record.duration_days)
            else:
                record.due_date = False

    @api.constrains('vehicle_number', 'customer_id', 'start_date')
    def _check_unique_vehicle_number(self):
        for record in self:
            if record.vehicle_number and record.customer_id and record.start_date:
                existing_records = self.env['vehicle.repair'].search([
                    ('vehicle_number', '=', record.vehicle_number),
                    ('customer_id', '=', record.customer_id.id),
                    ('start_date', '=', record.start_date),
                    ('id', '!=', record.id),
                ])
                if existing_records:
                    raise exceptions.ValidationError(_('Vehicle number must be unique for today and customer!'))


class LabourCost(models.Model):
    _name = "labour.cost"
    _description = "Labour Cost"

    labour_id = fields.Many2one('hr.employee', string="Labour", required=True)
    hourly_cost = fields.Monetary(string="Cost", related='labour_id.hourly_cost', currency_field='currency_id',
                                  store=True)
    hour_spend = fields.Float(string="Hour Spend", default=0.0)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    sub_total = fields.Monetary(string="Sub Total", compute='_compute_sub_total', store=True)
    vehicles_type_id = fields.Many2one('vehicle.repair', string="Vehicle Type")

    @api.depends('hour_spend', 'hourly_cost')
    def _compute_sub_total(self):
        for record in self:
            record.sub_total = record.hour_spend * record.hourly_cost


class ConsumedParts(models.Model):
    _name = "consumed.parts"
    _description = "Consumed Parts"

    product_id = fields.Many2one('product.product', string="Product", required=True,
                                 domain="[('type', 'in', ['product', 'consu'])]")
    quantity = fields.Float(string="Quantity", required=True, default=1)
    unit_price = fields.Float(string="Unit Price", related='product_id.lst_price', required=True, readonly=False)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    subtotal = fields.Monetary(string="Subtotal", compute='_compute_subtotal', store=True)
    vehicles_type_id = fields.Many2one('vehicle.repair', string="Vehicle Type")

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.unit_price

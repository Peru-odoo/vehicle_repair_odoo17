# -*- coding: utf-8 -*-
from odoo import models, fields


class RepairTag(models.Model):
    _name = "repair.tag"
    _description = " Repair Tags"

    name = fields.Char(string="Tags")
    color = fields.Char(string="Color")

    def action_get_result(self, data):
        print(data)
        print("---------------------------------------------")
        return "****************************"

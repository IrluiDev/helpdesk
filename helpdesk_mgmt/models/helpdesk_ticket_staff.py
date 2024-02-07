# Copyright 2024 Alda Hotels - Irlui Ramírez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HelpdeskTicketStaff(models.Model):

    _name = "helpdesk.ticket.staff"
    _description = "Helpdesk Ticket Staff"
    _order = "sequence, id"
    sequence = fields.Integer(default=10)
    name = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

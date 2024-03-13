# Copyright 2024 Alda Hotels - Irlui Ramírez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HelpdeskTicketoffice(models.Model):

    _name = "helpdesk.ticket.office"
    _description = "Helpdesk Ticket office"
    _order = "sequence, id"
    sequence = fields.Integer(default=10)
    name = fields.Char(
        string="Office Name",
        help="Office Name",
        required=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        string="Company",
        help="The company that owns or operates this property.",
        comodel_name="res.company",
        index=True,
        required=True,
    )

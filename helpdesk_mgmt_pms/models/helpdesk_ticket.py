from odoo import api, fields, models


class HelpdeskTicket(models.Model):

    _inherit = "helpdesk.ticket"

    property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        domain="[('company_id', '=', company_id)]",
        help="The hotel associated with this ticket",
    )
    room_id = fields.Many2one(
        comodel_name="pms.room",
        string="Room",
        domain="[('pms_property_id', '=', property_id)]",
        help="The room associated with this ticket",
        widget="many2one_tags",
    )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id:
            # Utilizar sudo para acceder al modelo pms.property y filtrar por usuario actual
            hotels = (
                self.env["pms.property"]
                .sudo()
                .search([("user_ids", "=", self.env.user.id)])
            )
            hotel_ids = hotels.ids if hotels else []
            return {"domain": {"property_id": [("id", "in", hotel_ids)]}}
        else:
            return {"domain": {"property_id": []}}

    @api.onchange("property_id")
    def _onchange_hotel_id(self):
        if self.hotel_id:
            # Utilizar sudo para acceder al modelo pms.room y filtrar por pms_property_id
            rooms = (
                self.env["pms.room"]
                .sudo()
                .search([("pms_property_id", "=", self.hotel_id.id)])
            )
            room_ids = rooms.ids if rooms else []
            return {"domain": {"room_id": [("id", "in", room_ids)]}}
        else:
            return {"domain": {"room_id": []}}

import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class HelpdeskTicketController(http.Controller):
    @http.route("/ticket/close", type="http", auth="user", website=True)
    def support_ticket_close(self, **kw):
        """Close the support ticket"""
        values = {}
        for field_name, field_value in kw.items():
            if field_name.endswith("_id"):
                values[field_name] = int(field_value)
            else:
                values[field_name] = field_value
        ticket = (
            http.request.env["helpdesk.ticket"]
            .sudo()
            .search([("id", "=", values["ticket_id"])])
        )
        stage = http.request.env["helpdesk.ticket.stage"].browse(values.get("stage_id"))
        if stage.close_from_portal:  # protect against invalid target stage request
            ticket.stage_id = values.get("stage_id")

        return werkzeug.utils.redirect("/my/ticket/" + str(ticket.id))

    def _get_teams(self):
        return (
            http.request.env["helpdesk.ticket.team"]
            .with_company(request.env.company.id)
            .search([("active", "=", True), ("show_in_portal", "=", True)])
            if http.request.env.user.company_id.helpdesk_mgmt_portal_select_team
            else False
        )

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        # Obtener el usuario actual
        user = request.env.user
        # Verificar si el usuario pertenece al grupo helpdesk_mgmt.group_helpdesk_user_team
        user_belongs_to_group = user.has_group('helpdesk_mgmt.group_helpdesk_user_team' or 'helpdesk_mgmt.group_helpdesk_manager')
        # Obtener las compañías asignadas al usuario actual
        assigned_companies = user.company_ids
        company = request.env.company
        category_model = http.request.env["helpdesk.ticket.category"]
        categories = category_model.with_company(company.id).search(
            [("active", "=", True)]
        )
        tag_model = http.request.env["helpdesk.ticket.tag"]
        tags = tag_model.with_company(company.id).search([("active", "=", True)])
        email = http.request.env.user.email
        name = http.request.env.user.name
        hotel_model = http.request.env["pms.property"]
        hotels = hotel_model.sudo().search(
            [("user_ids", "in", [http.request.env.user.id])]
        )
        all_room_ids = [room_id for hotel in hotels for room_id in hotel.room_ids.ids]

        room_model = http.request.env["pms.room"]
        rooms = room_model.sudo().search(
            [("id", "in", all_room_ids)]
        )
        return http.request.render(
            "helpdesk_mgmt.portal_create_ticket",
            {
                "user_belongs_to_group": user_belongs_to_group,
                "companies": assigned_companies,
                "categories": categories,
                "teams": self._get_teams(),
                "hotels": hotels,
                "rooms": rooms,
                "tags": tags,
                "email": email,
                "name": name,
                "ticket_team_id_required": (
                    company.helpdesk_mgmt_portal_team_id_required
                ),
                "ticket_category_id_required": (
                    company.helpdesk_mgmt_portal_category_id_required
                ),
            },
        )

    def _prepare_submit_ticket_vals(self, **kw):
        category = http.request.env["helpdesk.ticket.category"].browse(
            int(kw.get("category"))
        )
        selected_company = kw.get("company_id")
        if selected_company is None: company = http.request.env.user.company_id
        else: company = http.request.env["res.company"].sudo().browse(int(selected_company))
        is_office = False
        office_id = False
        hotel_id = False
        
        if company.id == 6:
            is_office = True
            office_id = request.params.get('hotel_id')
        else:
            hotel_id = request.params.get('hotel_id')
        vals = {
            "company_id": company.id,
            "category_id": category.id,
            "hotel_id": hotel_id,
            "room_id": request.params.get('room_id'),
            "description": plaintext2html(kw.get("description")),
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env["helpdesk.ticket.channel"]
            .sudo()
            .search([("name", "=", "Web")])
            .id,
            "partner_id": request.env.user.partner_id.id,
            "partner_name": request.env.user.partner_id.name,
            "partner_email": request.env.user.partner_id.email,
            # Need to set stage_id so that the _track_template() method is called
            # and the mail is sent automatically if applicable
            "stage_id": request.env["helpdesk.ticket"]
            .with_company(company.id)
            .default_get(["stage_id"])["stage_id"],
            "is_office":is_office,
            "office_id":office_id,
        }
        if company.helpdesk_mgmt_portal_select_team and kw.get("team"):
            team = (
                http.request.env["helpdesk.ticket.team"]
                .sudo()
                .search(
                    [("id", "=", int(kw.get("team"))), ("show_in_portal", "=", True)]
                )
            )
            vals.update({"team_id": team.id})
        return vals

    @http.route("/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    def submit_ticket(self, **kw):
        vals = self._prepare_submit_ticket_vals(**kw)
        new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "helpdesk.ticket",
                            "res_id": new_ticket.id,
                        }
                    )
        return werkzeug.utils.redirect("/my/ticket/%s" % new_ticket.id)

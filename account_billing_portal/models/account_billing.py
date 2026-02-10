# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountBilling(models.Model):
    _inherit = ["account.billing", "portal.mixin"]
    _name = "account.billing"

    def _compute_access_url(self):
        super()._compute_access_url()
        for billing in self:
            billing.access_url = f"/my/billings/{billing.id}"
        return

    def _get_report_base_filename(self):
        self.ensure_one()
        return f"BILL-{self.name}"

    def action_billing_send(self):
        self.ensure_one()
        ir_model_data = self.env["ir.model.data"]
        try:
            template_id = ir_model_data._xmlid_lookup(
                "account_billing_portal.email_template_billing"
            )[1]
        except ValueError:
            template_id = False
        if not template_id:
            return
        try:
            compose_form_id = ir_model_data._xmlid_lookup(
                "mail.email_compose_message_wizard_form"
            )[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        report_template = self.company_id.billing_portal_report or self.env.ref(
            "account_billing.report_account_billing"
        )
        template = self.env["mail.template"].browse(template_id)
        template.report_template_ids = report_template.ids
        email_xml_id = "mail.mail_notification_layout_with_responsible_signature"
        ctx.update(
            {
                "default_model": "account.billing",
                "default_res_ids": self.ids,
                "default_template_id": template_id,
                "default_composition_mode": "comment",
                "default_email_layout_xmlid": email_xml_id,
                "email_notification_allow_footer": True,
                "force_email": True,
            }
        )
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
        }

    def preview_billing(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }

    def validate_billing(self):
        res = super().validate_billing()
        for rec in self.filtered(lambda x: x.state == "billed"):
            subscribers = (
                [rec.partner_id.id]
                if rec.partner_id not in rec.message_partner_ids
                else None
            )
            rec.message_subscribe(subscribers)
        return res

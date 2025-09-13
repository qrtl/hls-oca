# Copyright 2025 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

class WebFormBannerRule(models.Model):
    _name = "web_form_banner.rule"
    _description = "Form Banner Rule"

    model_id = fields.Many2one("ir.model", ondelete="cascade", required=True)
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    view_ids = fields.Many2many(
        "ir.ui.view",
        domain="[('type', '=', 'form'), ('model', '=', model_name)]",
        help="Form view where the banner should be injected."
    )
    message = fields.Html(required=True)
    severity = fields.Selection(
        [("info", "Info"), ("warning", "Warning"), ("danger", "Danger")],
        default="danger",
        required=True,
    )
    xpath = fields.Char(
        default='//sheet',
        help="XPath of the node to insert the banner BEFORE."
    )
    message_domain = fields.Char(
        help="Optional domain to filter records where the banner is shown. "
        "E.g. [('state', '=', 'draft')]."
    )
    active = fields.Boolean(default=True)

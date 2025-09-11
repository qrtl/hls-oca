# Copyright 2025 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

class WebFormBannerRule(models.Model):
    _name = "web_form_banner.rule"
    _description = "Form Banner Rule"

    view_id = fields.Many2one(
        "ir.ui.view", required=True,
        domain=[('type', '=', 'form')],
        help="Form view where the banner should be injected."
    )
    message = fields.Html(required=True)
    severity = fields.Selection(
        [("info", "info"), ("warning", "warning"), ("danger", "danger")],
        default="danger",
        required=True,
    )
    xpath = fields.Char(
        default='//sheet',
        help="XPath of the node to insert the banner BEFORE."
    )
    field_name = fields.Char(
        help="Optional field on the record controlling visibility. "
        "If boolean: show when True. If char/text: show when non-empty. "
        "Leave empty to always show."
    )
    invert = fields.Boolean(
        help="Invert visibility logic: show when field is False/empty."
    )
    active = fields.Boolean(default=True)

# Copyright 2025 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import api, fields, models, tools
from odoo.tools.safe_eval import safe_eval
from odoo.tools import html_escape


class WebFormBannerRule(models.Model):
    _name = "web_form_banner.rule"
    _description = "Form Banner Rule"
    _order = "sequence, id"

    model_id = fields.Many2one("ir.model", ondelete="cascade", required=True)
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    view_ids = fields.Many2many(
        "ir.ui.view",
        domain="[('type', '=', 'form'), ('model', '=', model_name)]",
        help="Form view where the banner should be injected. If empty, applies to all "
        "views of the model.",
    )
    # message = fields.Html()
    severity = fields.Selection(
        [("info", "Info"), ("warning", "Warning"), ("danger", "Danger")],
        default="danger",
        required=True,
    )
    xpath = fields.Char(
        "XPath",
        default="//sheet",
        help="XPath of the node to insert the banner BEFORE."
    )
    message_domain = fields.Char(
        help="Optional domain to filter records where the banner is shown. "
        "E.g. [('state', '=', 'draft')].",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    message_template = fields.Text(
        translate=True,
        required=True,
        help="Template with placeholders. Use either %(key)s or {key} style."
    )
    message_values_expr = fields.Text(
        "Value Expression",
        help="Python expression returning a dict used to fill the template. "
        "Env: record, env, user, ctx. Example: "
        "{'class': (record.partner_id.comment or '').strip()}",
    )
    message_is_html = fields.Boolean(
        "Message is HTML",
        help="If enabled, the rendered message is treated as HTML. If disabled, "
        "it will be escaped; line-breaks are preserved.",
    )

    @api.model
    def render_message(self, rule_id, model, res_id):
        rule = self.sudo().browse(rule_id)
        if not rule or not res_id:
            return ""
        record = self.env[model].browse(res_id)
        # Build the values dict safely
        localdict = {
            "env": self.env,
            "user": self.env.user,
            "ctx": dict(self.env.context),
            "record": record,
        }
        values = {}
        if rule.message_values_expr and rule.message_values_expr.strip():
            try:
                result = safe_eval(rule.message_values_expr.strip(), localdict) or {}
                if isinstance(result, dict):
                    # ensure string keys
                    values = {str(k): ("" if v is None else v) for k, v in result.items()}
            except Exception:
                values = {}
        lang = self.env.user.lang or self.env.context.get("lang")
        template = (rule.with_context(lang=lang).message_template or "").strip()
        # Render with tolerant formatting: support both %(k)s and {k}
        text = ""
        try:
            if "%(" in template:
                # %-style
                text = template % defaultdict(str, values)
            else:
                # {key}-style
                class _MissingDict(defaultdict):
                    def __missing__(self, key): return ""
                text = template.format_map(_MissingDict(str, values))
        except Exception:
            # No crashing on errors
            text = ""
        text = tools.ustr(text or "")
        if rule.message_is_html:
            # return as-is (JS uses .html(...))
            return text
        # Escape + preserve line breaks; your span uses white-space: normal
        return html_escape(text).replace("\n", "<br/>")

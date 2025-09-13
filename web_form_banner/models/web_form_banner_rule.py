# Copyright 2025 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from string import Template

class WebFormBannerRule(models.Model):
    _name = "web.form.banner.rule"
    _description = "Form Banner Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    model_id = fields.Many2one("ir.model", ondelete="cascade", required=True)
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    view_ids = fields.Many2many(
        "ir.ui.view",
        domain="[('type', '=', 'form'), ('model', '=', model_name)]",
        help="Form view where the banner should be injected.",
    )
    message = fields.Html(required=True, help="HTML template. You can use ${placeholders}.")
    severity = fields.Selection(
        [("info", "Info"), ("warning", "Warning"), ("danger", "Danger")],
        default="danger",
        required=True,
    )
    xpath = fields.Char(
        default="//sheet",
        help="XPath of the node to insert the banner BEFORE.",
    )
    # New: Python expression returning a dict controlling visibility/content.
    # Example return:
    #   {"visible": True, "severity": "warning", "values": {"title": "..."}, "html": "<b>...</b>"}
    message_values_expr = fields.Text(
        help=(
            "Python expression evaluated server-side. Must return a dict.\n"
            "Keys: visible(bool, default True), severity(str), values(dict for ${...} in message),\n"
            "and/or html(str) to override template rendering."
        )
    )
    # Optional: comma-separated fields the client should treat as dependencies for live recompute.
    depends_fields = fields.Char(
        help="Comma-separated field names to watch for live updates (e.g., 'partner_id,payment_term_id')."
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # used by JS
    @api.model
    def compute_message(self, rule_id, model, res_id):
        """Return {visible, severity, html} for the given rule and record."""
        rule = self.browse(int(rule_id)).sudo()
        if not rule.exists() or not rule.active:
            return {"visible": False}
        record = self.env[model].browse(int(res_id)) if res_id else self.env[model]
        # Build safe eval context
        ctx = {
            "env": self.env,
            "user": self.env.user,
            "ctx": dict(self.env.context),
            "record": record,
        }

        # helper: build form URL for a record
        def _url_for(rec):
            try:
                if not rec or not getattr(rec, "id", None):
                    return ""
                base = self.env["ir.config_parameter"].sudo().get_param("web.base.url", default="")
                return "%s/web#id=%d&model=%s&view_type=form" % (base, rec.id, rec._name)
            except Exception:
                return ""
        ctx.update({"url_for": _url_for})

        visible = True
        severity = rule.severity or "danger"
        values = {}
        html = None
        if rule.message_values_expr:
            code = rule.message_values_expr.strip()
            try:
                # 1) try single-expression dict
                out = safe_eval(code, ctx, mode="eval") or {}
            except Exception:
                # 2) allow multi-line; expect `result` to be set
                #    IMPORTANT: nocopy=True so assignments write back into ctx
                safe_eval(code, ctx, mode="exec", nocopy=True)
                out = ctx.get("result") or {}
            if not isinstance(out, dict):
                return {"visible": False}
            # pull control keys
            visible = out.get("visible", True)
            severity = out.get("severity", severity)
            values = out.get("values", {})
            html = out.get("html")
            # convenience: if no explicit `values`, treat other keys as template vars
            if not values:
                values = {k: v for k, v in out.items() if k not in {"visible", "severity", "values", "html"}}

        if not visible:
            return {"visible": False}
        # Render html using template if not provided directly
        if not html:
            tpl = Template(rule.message or "")
            try:
                html = tpl.safe_substitute(values)
            except Exception:
                html = rule.message or ""
        return {"visible": True, "severity": severity, "html": html}

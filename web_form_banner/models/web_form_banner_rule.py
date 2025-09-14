# Copyright 2025 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree
from string import Template

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import html_escape


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
    target_xpath = fields.Char(
        "Target XPath",
        default="//sheet",
        help="XPath of the node to insert the banner.",
    )
    position = fields.Selection(
        [("before", "Before target"), ("after", "After target")],
        string="Position",
        default="before",
        required=True,
        help="Where to insert the placeholder relative to the first matched node."
    )
    severity = fields.Selection(
        [("info", "Info"), ("warning", "Warning"), ("danger", "Danger")],
        default="danger",
        required=True,
    )
    message = fields.Text(
        help="Template with ${placeholders}. If not HTML, it will be escaped. ",
    )
    message_is_html = fields.Boolean(
        "HTML",
        help="If checked, 'message' is treated as raw HTML (no escaping). "
        "If not checked, the rendered text is escaped and newlines become <br/>."
    )
    # Example return:
    #   {"visible": True, "severity": "warning", "values": {"title": "..."}, "html": "<b>...</b>"}
    message_value_code = fields.Text(
        help=(
            "Python expression evaluated server-side. Must return a dict.\n"
            "Keys: visible(bool, default True), severity(str), values(dict for ${...} in message),\n"
            "and/or html(str) to override template rendering."
        )
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    @api.constrains("target_xpath")
    def _check_target_xpath(self):
        for rec in self:
            xp = (rec.target_xpath or "").strip()
            try:
                etree.XPath(xp or "//sheet")
            except (etree.XPathSyntaxError, etree.XPathEvalError) as e:
                raise ValidationError("Invalid XPath:\n%s" % e)

    @api.model
    def _build_form_url(self, rec):
        try:
            if not rec or not getattr(rec, "id", None):
                return ""
            base = self.env["ir.config_parameter"].sudo().get_param("web.base.url", default="")
            return "%s/web#id=%d&model=%s&view_type=form" % (base, rec.id, rec._name)
        except Exception:
            return ""

    @api.model
    def _get_safe_eval_context(self, record):
        return {
            "env": self.env,
            "user": self.env.user,
            "ctx": dict(self.env.context),
            "record": record,
            "url_for": self._build_form_url,
        }

    @api.model
    def compute_message(self, rule_id, model, res_id):
        """Return {visible, severity, html} for the given rule and record."""
        rule = self.browse(int(rule_id)).sudo()
        if not rule.exists() or not rule.active:
            return {"visible": False}
        record = self.env[model].browse(int(res_id)) if res_id else self.env[model]
        ctx = self._get_safe_eval_context(record)
        visible = True
        severity = rule.severity or "danger"
        values = {}
        html = None
        if rule.message_value_code:
            code = rule.message_value_code.strip()
            try:
                # 1) try single-expression dict
                out = safe_eval(code, ctx, mode="eval") or {}
            except Exception:
                # 2) allow multi-line; expect `result` to be set
                safe_eval(code, ctx, mode="exec", nocopy=True)
                out = ctx.get("result") or {}
            if not isinstance(out, dict):
                return {"visible": False}
            visible = out.get("visible", True)
            severity = out.get("severity", severity)
            values = out.get("values", {})
            html = out.get("html")
            # If no explicit `values`, treat other keys as template vars
            if not values:
                values = {
                    k: v for k, v in out.items() if k not in {
                        "visible", "severity", "values", "html"
                    }
                }
        if not visible:
            return {"visible": False}
        # Render html using template if not provided directly
        if not html:
            tpl = Template(rule.message or "")
            try:
                rendered = tpl.safe_substitute(values)
            except Exception:
                rendered = rule.message or ""
            if rule.message_is_html:
                html = rendered
            else:
                html = html_escape(rendered).replace("\n", "<br/>")
        return {"visible": True, "severity": severity, "html": html}

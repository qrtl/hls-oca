# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import time
import datetime as dt
from dateutil import parser as dateparse
from dateutil.relativedelta import relativedelta
from pytz import timezone

from functools import lru_cache
from lxml import etree
from string import Template

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html_escape
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.safe_eval import safe_eval


class WebFormBannerRule(models.Model):
    _name = "web.form.banner.rule"
    _description = "Form Banner Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    model_id = fields.Many2one("ir.model", ondelete="cascade", required=True)
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    view_ids = fields.Many2many(
        "ir.ui.view",
        string="Views",
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
        string="Default Severity",
        default="danger",
        required=True,
        help="Default severity level, can be overridden per-record.",
    )
    message = fields.Text(
        translate=True,
        help="Template with ${placeholders}. If not HTML, it will be escaped.",
    )
    message_is_html = fields.Boolean(
        "HTML",
        help="If checked, 'message' is treated as raw HTML (no escaping). "
        "If not checked, the rendered text is escaped and newlines become <br/>."
    )
    message_value_code = fields.Text(
        help="Python expression evaluated server-side. Must return a dict.\n"
        "Keys: visible(bool, default True), severity(str), values(dict for ${...} in \n"
        "message), and/or html(str) to override template rendering.",
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
                raise ValidationError(_("Invalid XPath:\n%s") % e)

    @api.model
    def _build_form_url(self, rec):
        try:
            if not rec or not getattr(rec, "id", None):
                return ""
            base = self.env["ir.config_parameter"].sudo().get_param(
                "web.base.url", default=""
            )
            return "%s/web#id=%d&model=%s&view_type=form" % (base, rec.id, rec._name)
        except Exception:
            return ""

    @lru_cache(maxsize=1)
    def _banner_base_eval_ctx_static(self):
        # Only static, import-heavy items
        return {
            "time": time,
            "datetime": dt,
            "dateutil": {
                "parser": dateparse,
                "relativedelta": relativedelta,
            },
            "timezone": timezone,
            "float_compare": float_compare,
            "float_is_zero": float_is_zero,
            "float_round": float_round,
        }

    @api.model
    def _get_banner_eval_context(self, record):
        eval_ctx = dict(self._banner_base_eval_ctx_static())
        eval_ctx.update(
            {
                "env": record.env,
                "user": record.env.user,
                "ctx": dict(record.env.context),
                "model": record.env[record._name],
                "record": record,
                "context_today": lambda ts=None: fields.Date.context_today(
                    record, timestamp=ts
                ),
                "url_for": self._build_form_url,
            }
        )
        return eval_ctx

    @api.model
    def compute_message(self, rule_id, model, res_id):
        """Return {visible, severity, html} for the given rule and record."""
        lang = self._context.get("lang") or self.env.user.lang
        self = self.with_context(lang=lang)
        rule = self.browse(int(rule_id)).sudo()
        if not rule.exists() or not rule.active:
            return {"visible": False}
        record = self.env[model].browse(int(res_id)) if res_id else self.env[model]
        eval_ctx = self._get_banner_eval_context(record)
        visible = True
        severity = rule.severity or "danger"
        values = {}
        html = None
        if rule.message_value_code:
            code = rule.message_value_code.strip()
            try:
                # 1) try single-expression dict
                out = safe_eval(code, eval_ctx, mode="eval") or {}
            except Exception:
                # 2) allow multi-line; expect `result` to be set
                safe_eval(code, eval_ctx, mode="exec", nocopy=True)
                out = eval_ctx.get("result") or {}
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

# Copyright 2025 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from lxml import etree
from odoo import api, models

class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def fields_view_get(self, view_id=None, view_type="form", toolbar=False, submenu=False):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type != "form" or not res.get("arch"):
            return res
        current_view_id = view_id or res.get("view_id")
        if not current_view_id:
            return res
        rules = self.env["web_form_banner.rule"].sudo().search(
            [("active", "=", True), ("view_id", "=", current_view_id)]
        )
        if not rules:
            return res
        try:
            root = etree.fromstring(res["arch"])
        except Exception:
            return res
        for rule in rules:
            targets = root.xpath(rule.xpath or "//sheet")
            if not targets:
                continue
            css = "alert alert-%s" % (rule.severity or "danger")
            banner = etree.Element("div", {"class": css, "role": "alert"})
            field = (rule.field_name or "").strip()
            if field and field in (res.get("fields") or {}):
                ftype = res["fields"][field].get("type")
                if ftype == "boolean":
                    invisible_domain = [(field, "=", True)] if rule.invert else [(field, "=", False)]
                else:
                    invisible_domain = [(field, "!=", False)] if rule.invert else [(field, "=", False)]
                banner.set("modifiers", json.dumps({"invisible": invisible_domain}))
                span = etree.SubElement(banner, "span")
                span.text = rule.message or ""
                # Insert BEFORE the first match of the target
                target = targets[0]
                parent = target.getparent()
                if parent is not None:
                    parent.insert(parent.index(target), banner)
        res["arch"] = etree.tostring(root, encoding="unicode")
        return res

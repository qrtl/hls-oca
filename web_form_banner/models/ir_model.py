# Copyright 2025 Quartile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from lxml import etree
from odoo import api, models
from odoo.tools.safe_eval import safe_eval


# helpers
def _collect_domain_fields(tokens):
    names = set()
    for t in tokens or []:
        if t in ('|', '&', '!'):
            continue
        if isinstance(t, (list, tuple)) and t and isinstance(t[0], str):
            if t[0] not in ('|', '&', '!'):
                names.add(t[0])
    return names

def _or_tokens(parts):
    """OR together multiple token lists into one flat token list."""
    parts = [p for p in parts if p]  # drop empties
    if not parts:
        return []  # means "always visible"
    if len(parts) == 1:
        return parts[0]
    # prefix '|' (n-1) times, then concatenate all tokens
    return ['|'] * (len(parts) - 1) + [tok for p in parts for tok in p]


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
            [
                ("model_name", "=", self._name),
                "|",
                ("view_ids", "in", current_view_id),
                ("view_ids", "=", False),
            ]
        )
        if not rules:
            return res
        try:
            root = etree.fromstring(res["arch"])
        except Exception:
            return res
        form_node = root if root.tag == "form" else (root.xpath("//form") or [root])[0]
        for rule in rules:
            targets = root.xpath(rule.xpath or "//sheet")
            if not targets:
                continue
            css = "alert alert-%s" % (rule.severity or "danger")
            attrs = {"class": css, "role": "alert"}
            # tag for dynamic fetch
            attrs["data-wfb-rule-id"] = str(rule.id)
            attrs["data-wfb-model"] = self._name
            # start hidden; JS will show when non-empty
            attrs["style"] = "display:none;"
            banner = etree.Element("div", attrs)
            span = etree.SubElement(banner, "span", {"style": "white-space: pre-line;"})
            span.text = (rule.message_template or u"\u00A0")
            invisible_parts = []  # each element is a FLAT token list
            # message_domain -> tokens for NOT(message_domain)
            if rule.message_domain:
                try:
                    dom_show = safe_eval(rule.message_domain.strip(), {
                        'uid': self.env.uid,
                        'user': self.env.user,
                        'context': dict(self.env.context),
                    })
                except Exception:
                    dom_show = None
                if isinstance(dom_show, (list, tuple)) and dom_show:
                    # ensure fields used by the domain are available
                    for fname in _collect_domain_fields(dom_show):
                        if fname in self._fields and fname not in (res.get('fields') or {}):
                            hidden = etree.Element("field", {"name": fname, "invisible": "1", "nolabel": "1"})
                            form_node.insert(0, hidden)
                            res.setdefault("fields", {}).update(self.fields_get([fname]))
                    # NOT(dom_show) as FLAT tokens
                    invisible_parts.append(['!'] + list(dom_show))
            # Combine with OR (hide if ANY invisibility reason holds)
            invisible_tokens = _or_tokens(invisible_parts)
            if invisible_tokens:
                banner.set("modifiers", json.dumps({"invisible": invisible_tokens}))
            # Insert BEFORE the first target
            parent = targets[0].getparent()
            if parent is not None:
                parent.insert(parent.index(targets[0]), banner)
        res["arch"] = etree.tostring(root, encoding="unicode")
        return res

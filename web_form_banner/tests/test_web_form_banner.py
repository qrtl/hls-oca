# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from lxml import etree

from odoo.tests.common import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestFieldsViewGetPartnerBanner(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.Rule = cls.env["web.form.banner.rule"].search([
            ("model_name", "=", "res.partner"),
            ("active", "=", True),
        ], limit=1)
        if not cls.Rule:
            raise AssertionError(
                "Expected a demo web.form.banner.rule for res.partner (active=True) "
                "but none was found. Ensure demo data is loaded."
            )

        cls.partner_form_view = cls.env.ref("base.view_partner_form")

    # ---- helpers ----

    def _get_arch_tree_for_partner(self):
        """Return (arch_str, etree) for partner form with the demo rule applied."""
        res = self.Partner.fields_view_get(
            view_id=self.partner_form_view.id,
            view_type="form",
            toolbar=False,
            submenu=False,
        )
        arch = res["arch"]
        return arch, etree.fromstring(arch)

    def _find_banner_node(self, tree):
        """Find the injected placeholder node for our rule."""
        xpath = "//div[@data-rule-id='%s' and contains(@class,'o_form_banner')]" % self.Rule.id
        nodes = tree.xpath(xpath)
        self.assertTrue(nodes, "Expected banner node injected in the form arch.")
        return nodes[0]

    def _code(self):
        return (self.Rule.message_value_code or "").strip()

    # ---- tests ----

    def test_injected_once_with_expected_attrs(self):
        arch, tree = self._get_arch_tree_for_partner()
        node = self._find_banner_node(tree)

        # Basic attributes from the server injection
        # (see web_form_banner/models/ir_model.py)
        self.assertEqual(node.get("data-model"), "res.partner")
        self.assertEqual(node.get("data-default-severity"), (self.Rule.severity or "danger"))
        self.assertEqual(node.get("role"), "alert")
        self.assertEqual(node.get("style"), "display:none;")

        # Class list includes the expected CSS classes
        classes = (node.get("class") or "").split()
        for required in ("o_form_banner", "alert", "alert-%s" % (self.Rule.severity or "danger")):
            self.assertIn(required, classes)

        # Ensure it's not duplicated
        all_banners = tree.xpath("//div[contains(@class,'o_form_banner')]")
        self.assertEqual(
            len(all_banners), 1,
            "Expected exactly one banner placeholder to be injected for res.partner"
        )

    def test_position_relative_to_sheet(self):
        _, tree = self._get_arch_tree_for_partner()
        node = self._find_banner_node(tree)

        # First visible <sheet> node in the form
        sheets = tree.xpath("//sheet")
        self.assertTrue(sheets, "Expected a <sheet> in the partner form view")
        sheet = sheets[0]

        # Both banner and sheet should share the same parent
        parent = sheet.getparent()
        self.assertIsNotNone(parent, "Sheet must have a parent")
        self.assertIs(parent, node.getparent(), "Banner and sheet should share the same parent")

        siblings = list(parent)
        i_sheet = siblings.index(sheet)
        i_node = siblings.index(node)

        pos = (self.Rule.position or "before")
        if pos == "before":
            self.assertEqual(
                i_node, i_sheet - 1,
                "Banner should be inserted immediately before <sheet> when position='before'"
            )
        else:  # 'after'
            self.assertEqual(
                i_node, i_sheet + 1,
                "Banner should be inserted immediately after <sheet> when position='after'"
            )

    def test_not_injected_on_unrelated_model(self):
        # Sanity: pick a base model without a rule (res.company is present in base)
        Company = self.env["res.company"]
        # Use the standard company form view
        view = self.env.ref("base.view_company_form")
        res = Company.fields_view_get(view_id=view.id, view_type="form")
        tree = etree.fromstring(res["arch"])
        self.assertFalse(
            tree.xpath("//div[contains(@class,'o_form_banner')]"),
            "No banners should be injected on models without active rules",
        )

    def test_contains_expected_messages_and_severities(self):
        code = self._code()
        # Messages
        self.assertRegex(
            code,
            r"This partner['’]s name is very long!",
            "Missing 'very long' message literal in message_value_code",
        )
        self.assertRegex(
            code,
            r"This partner['’]s name is a bit long\.",
            "Missing 'bit long' message literal in message_value_code",
        )
        # Severities
        self.assertRegex(code, r"['\"]danger['\"]", "Missing 'danger' severity literal")
        self.assertRegex(code, r"['\"]warning['\"]", "Missing 'warning' severity literal")

    def test_trims_whitespace_before_length_check(self):
        code = self._code()
        # Tolerate different styles, but insist .strip() is used on the name
        self.assertRegex(code, r"\.strip\(\)", "Expected .strip() usage before length check")

    def test_length_thresholds_present_and_ordered(self):
        code = self._code()
        # Accept either `n = len(name)` then `n > X` or inline `len(name) > X`
        pat20 = re.search(r"(?:\bn\s*>\s*20\b|len\s*\(\s*name\s*\)\s*>\s*20)", code)
        pat10 = re.search(r"(?:\bn\s*>\s*10\b|len\s*\(\s*name\s*\)\s*>\s*10)", code)
        self.assertIsNotNone(pat20, "Missing > 20 threshold check")
        self.assertIsNotNone(pat10, "Missing > 10 threshold check")
        # Ensure the '> 20' branch is evaluated before '> 10' (so 21+ shows 'danger')
        self.assertLess(
            pat20.start(), pat10.start(),
            "Expected the '> 20' branch to precede the '> 10' branch",
        )

    def test_result_object_keys_are_declared(self):
        code = self._code()
        # Sanity: ensure the code sets a result mapping with common keys
        self.assertIn("result", code, "Expected a 'result' variable to be assigned")
        for key in ("visible", "severity", "html"):
            self.assertIn(key, code, "Expected '%s' key to appear in result dict" % key)

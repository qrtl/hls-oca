# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    billing_portal_report = fields.Many2one(
        "ir.actions.report",
        domain="[('model', '=', 'account.billing')]",
        help="This report template will be used in the billing portal to "
        "show the billing.",
    )

    def write(self, vals):
        res = super().write(vals)
        template = self.env.ref(
            "account_billing_portal.email_template_billing", raise_if_not_found=False
        )
        if not template:
            return res
        for company in self:
            if company.billing_portal_report:
                template.write(
                    {
                        "report_template_ids": [
                            (6, 0, [company.billing_portal_report.id])
                        ]
                    }
                )
        return res

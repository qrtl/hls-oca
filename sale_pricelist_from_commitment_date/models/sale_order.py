# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_require_commitment_date = fields.Boolean(
        related="company_id.sale_require_commitment_date"
    )
    sale_commitment_date_in_header = fields.Boolean(
        related="company_id.sale_commitment_date_in_header"
    )

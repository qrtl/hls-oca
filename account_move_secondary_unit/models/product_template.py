# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    account_move_secondary_uom_id = fields.Many2one(
        comodel_name="product.secondary.unit",
        string="Default secondary unit for invoices",
        domain="[('product_tmpl_id', '=', id), ('product_id', '=', False)]",
        compute="_compute_account_move_secondary_uom_id",
        inverse="_inverse_account_move_secondary_uom_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_variant_ids.account_move_secondary_uom_id")
    def _compute_account_move_secondary_uom_id(self):
        self._compute_template_secondary_uom_field("account_move_secondary_uom_id")

    def _inverse_account_move_secondary_uom_id(self):
        self._inverse_template_secondary_uom_field("account_move_secondary_uom_id")

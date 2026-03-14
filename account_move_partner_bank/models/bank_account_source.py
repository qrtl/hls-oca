# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from operator import attrgetter

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BankAccountSource(models.Model):
    _name = "bank.account.source"
    _description = "Bank Account Source"
    _order = "sequence, id"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    source_model_id = fields.Many2one(
        comodel_name="ir.model",
        required=True,
        ondelete="cascade",
        help="The model from which the bank field path is resolved.",
    )
    bank_field_path = fields.Char(
        required=True,
        help="Field path to res.partner.bank (e.g. partner_id.bank_account_id).",
    )

    @api.constrains("source_model_id", "bank_field_path")
    def _check_bank_field_path(self):
        for rec in self:
            parts = [p.strip() for p in rec.bank_field_path.split(".") if p.strip()]
            model = self.env[rec.source_model_id.model]
            for attr in parts[:-1]:
                field = model._fields.get(attr)
                if not field or field.type != "many2one":
                    raise ValidationError(
                        _("Invalid bank field path: %s") % rec.bank_field_path
                    )
                model = self.env[field.comodel_name]
            last = model._fields.get(parts[-1])
            if (
                not last
                or last.type != "many2one"
                or last.comodel_name != "res.partner.bank"
            ):
                raise ValidationError(
                    _("Invalid path (last field must reference res.partner.bank): %s")
                    % rec.bank_field_path
                )

    def get_bank_for_record(self, record):
        """Find bank from sources for the given record."""
        record.ensure_one()
        sources = self.filtered(lambda s: s.source_model_id.model == record._name)
        for source in sources:
            bank = attrgetter(source.bank_field_path)(record) or False
            if bank:
                return bank
        return False

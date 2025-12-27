# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("bank_partner_id", "partner_id")
    def _compute_partner_bank_id(self):
        super()._compute_partner_bank_id()
        for move in self:
            bank = move.company_id.bank_account_source_ids.get_bank_for_record(move)
            if bank:
                move.partner_bank_id = bank
        return

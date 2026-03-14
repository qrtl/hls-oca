# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAccountPartnerBank(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        # Remove existing bank accounts from demo data
        cls.env["res.partner.bank"].search(
            [("partner_id", "=", cls.company.partner_id.id)]
        ).unlink()
        cls.bank_account_1 = cls.env["res.partner.bank"].create(
            {
                "acc_number": "11110000",
                "partner_id": cls.company.partner_id.id,
                "company_id": cls.company.id,
                "sequence": 10,
            }
        )
        cls.bank_account_2 = cls.env["res.partner.bank"].create(
            {
                "acc_number": "22220000",
                "partner_id": cls.company.partner_id.id,
                "company_id": cls.company.id,
                "sequence": 20,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        account_move_model = cls.env.ref("account.model_account_move")
        cls.source = cls.env["bank.account.source"].create(
            {
                "company_id": cls.company.id,
                "sequence": 10,
                "source_model_id": account_move_model.id,
                "bank_field_path": "partner_id.bank_account_id",
            }
        )

    def create_invoice(self, partner):
        return self.env["account.move"].create(
            {"move_type": "out_invoice", "partner_id": partner.id}
        )

    def test_bank_field_path_constraint(self):
        # A random string
        with self.assertRaises(ValidationError):
            self.source.write({"bank_field_path": "test"})
        # Not a real field
        with self.assertRaises(ValidationError):
            self.source.write({"bank_field_path": "partner_id.bank_account"})
        # A real field but not many2one to res.partner.bank
        with self.assertRaises(ValidationError):
            self.source.write({"bank_field_path": "partner_id.country_id"})
        self.source.write({"bank_field_path": "commercial_partner_id.bank_account_id"})

    def test_account_move_partner_bank(self):
        # Odoo's default proposes bank_account_1 (lower sequence)
        move = self.create_invoice(self.partner)
        self.assertEqual(move.partner_bank_id, self.bank_account_1)
        # Assigning bank_account_id to partner supersedes Odoo's default
        self.partner.bank_account_id = self.bank_account_2
        move = self.create_invoice(self.partner)
        self.assertEqual(move.partner_bank_id, self.bank_account_2)

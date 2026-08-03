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
        cls.bank_account_3 = cls.env["res.partner.bank"].create(
            {
                "acc_number": "33330000",
                "partner_id": cls.company.partner_id.id,
                "company_id": cls.company.id,
                "sequence": 30,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.account_move_model = cls.env.ref("account.model_account_move")
        cls.source = cls.env["bank.account.source"].create(
            {
                "company_id": cls.company.id,
                "sequence": 20,
                "source_model_id": cls.account_move_model.id,
                "bank_field_path": "commercial_partner_id.bank_account_id",
            }
        )

    def create_contact_source(self):
        """Let the contact's own bank account take precedence."""
        return self.env["bank.account.source"].create(
            {
                "company_id": self.company.id,
                "sequence": 10,
                "source_model_id": self.account_move_model.id,
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
        self.source.write({"bank_field_path": "partner_id.bank_account_id"})

    def test_account_move_partner_bank(self):
        # Odoo's default proposes bank_account_1 (lower sequence)
        move = self.create_invoice(self.partner)
        self.assertEqual(move.partner_bank_id, self.bank_account_1)
        # Assigning bank_account_id to partner supersedes Odoo's default
        self.partner.bank_account_id = self.bank_account_2
        move = self.create_invoice(self.partner)
        self.assertEqual(move.partner_bank_id, self.bank_account_2)

    def test_bank_account_from_commercial_entity(self):
        # The bank account of the commercial entity applies to its contacts, without
        # being copied to them
        self.partner.bank_account_id = self.bank_account_2
        contact = self.env["res.partner"].create(
            {"name": "Test Contact", "parent_id": self.partner.id}
        )
        self.assertFalse(contact.bank_account_id)
        move = self.create_invoice(contact)
        self.assertEqual(move.partner_bank_id, self.bank_account_2)
        # An update on the commercial entity applies to the contacts as well
        self.partner.bank_account_id = self.bank_account_1
        move = self.create_invoice(contact)
        self.assertEqual(move.partner_bank_id, self.bank_account_1)

    def test_bank_account_contact_override(self):
        # A contact can collect on its own bank account (e.g. a branch), while the
        # other contacts of the company keep using the one of the commercial entity
        self.create_contact_source()
        self.partner.bank_account_id = self.bank_account_2
        branch, other_contact = self.env["res.partner"].create(
            [
                {
                    "name": "Test Branch",
                    "parent_id": self.partner.id,
                    "bank_account_id": self.bank_account_1.id,
                },
                {"name": "Test Contact", "parent_id": self.partner.id},
            ]
        )
        move = self.create_invoice(branch)
        self.assertEqual(move.partner_bank_id, self.bank_account_1)
        move = self.create_invoice(other_contact)
        self.assertEqual(move.partner_bank_id, self.bank_account_2)
        # An update on the commercial entity does not overwrite the branch
        self.partner.bank_account_id = self.bank_account_3
        self.assertEqual(branch.bank_account_id, self.bank_account_1)
        move = self.create_invoice(other_contact)
        self.assertEqual(move.partner_bank_id, self.bank_account_3)

    def test_bank_account_child_company(self):
        # A child company is its own commercial entity, so it keeps its bank account
        self.partner.bank_account_id = self.bank_account_2
        child_company = self.env["res.partner"].create(
            {
                "name": "Test Child Company",
                "parent_id": self.partner.id,
                "is_company": True,
                "bank_account_id": self.bank_account_1.id,
            }
        )
        move = self.create_invoice(child_company)
        self.assertEqual(move.partner_bank_id, self.bank_account_1)

    def test_bank_account_company_dependent(self):
        # The bank account is resolved in the company of the record, not in the one
        # of the environment
        other_company = self.env["res.company"].create({"name": "Test Company 2"})
        self.partner.bank_account_id = self.bank_account_2
        move = self.create_invoice(self.partner)
        bank = self.source.get_bank_for_record(move.with_company(other_company))
        self.assertEqual(bank, self.bank_account_2)

# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestSaleStockPartnerWarehouse(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env["base"].with_context(**DISABLED_MAIL_CONTEXT).env
        cls.warehouse_1 = cls.env["stock.warehouse"].create(
            {
                "name": "Base Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "ship_only",
                "code": "BWH",
            }
        )
        cls.warehouse_2 = cls.env["stock.warehouse"].create(
            {
                "name": "Test Warehouse",
                "reception_steps": "one_step",
                "delivery_steps": "ship_only",
                "code": "TWH",
            }
        )

    def test_sale_stock_partner_warehouse(self):
        partner = self.env.ref("base.res_partner_12")
        shipping_partner = self.env.ref("base.res_partner_12")
        partner.sale_warehouse_id = self.warehouse_1
        shipping_partner.sale_warehouse_id = self.warehouse_2
        with Form(self.env["sale.order"]) as order_form:
            order_form.partner_id = partner
        self.order = order_form.save()
        self.assertEqual(self.order.warehouse_id, partner.sale_warehouse_id)
        self.order.company_id.sale_warehouse_by_partner_shipping = True
        self.order.partner_shipping_id = shipping_partner
        self.assertEqual(self.order.warehouse_id, self.warehouse_2)

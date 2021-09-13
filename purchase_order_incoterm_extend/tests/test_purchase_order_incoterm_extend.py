# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests.common import SavepointCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseOrderIncotermExtend(SavepointCase):

    @classmethod
    def setUpClass(self):
        super(TestPurchaseOrderIncotermExtend, self).setUp()
        # Useful models
        self.PurchaseOrder = self.env['purchase.order']
        self.PurchaseOrderLine = self.env['purchase.order.line']
        self.AccountInvoice = self.env['account.invoice']
        self.AccountInvoiceLine = self.env['account.invoice.line']
        self.partner_id = self.env.ref('base.res_partner_1')
        self.product_id_1 = self.env.ref('product.product_product_8')
        self.product_id_2 = self.env.ref('product.product_product_11')

        (self.product_id_1 | self.product_id_2).write({'purchase_method': 'purchase'})
        self.po_vals = {
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_id_1.name,
                    'product_id': self.product_id_1.id,
                    'product_qty': 5.0,
                    'product_uom': self.product_id_1.uom_po_id.id,
                    'price_unit': 500.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }),
                (0, 0, {
                    'name': self.product_id_2.name,
                    'product_id': self.product_id_2.id,
                    'product_qty': 5.0,
                    'product_uom': self.product_id_2.uom_po_id.id,
                    'price_unit': 250.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                })],
        }

    def test_01_onchange_incoterm_place(self):
        self.order.order_line.write({
            'secondary_uom_id': self.secondary_unit.id,
            'secondary_uom_qty': 5,
        })
        self.order.order_line._onchange_secondary_uom()
        self.assertEqual(
            self.order.order_line.product_qty, 3.5)

    def test_02_incoterm_place_allow_empty(self):
        self.order.order_line.\
            _onchange_product_id_purchase_order_secondary_unit()
        self.assertEqual(
            self.order.order_line.secondary_uom_id, self.secondary_unit)

    def test_03_incoterm_place_able_to_update(self):

    def test_04_incoterm_place_validate_only_char_type(self):

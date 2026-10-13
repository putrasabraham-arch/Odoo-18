from odoo import Command
from odoo.tests import Form, TransactionCase


class TestPurchaseReceiptStatus(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Receipt Status Vendor"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Receipt Status Product A", "type": "consu"}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Receipt Status Product B", "type": "consu"}
        )
        cls.service = cls.env["product.product"].create(
            {"name": "Receipt Status Service", "type": "service"}
        )

    def _create_order(self, product_quantities):
        return self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_qty": quantity,
                            "product_uom": product.uom_po_id.id,
                        }
                    )
                    for product, quantity in product_quantities
                ],
            }
        )

    def _receive_with_backorder(self, picking, quantities):
        for product, quantity in quantities.items():
            move = picking.move_ids.filtered(lambda item: item.product_id == product)
            move.quantity = quantity
            move.picked = True
        action = picking.button_validate()
        if isinstance(action, dict):
            Form.from_action(self.env, action).save().process()

    def test_receipt_status_backorder_flow(self):
        order = self._create_order([(self.product_a, 10.0)])
        self.assertEqual(order.x_receipt_status, "not_received")

        order.button_confirm()
        self.assertEqual(order.x_receipt_status, "not_received")

        self._receive_with_backorder(order.picking_ids, {self.product_a: 4.0})
        self.assertEqual(order.order_line.qty_received, 4.0)
        self.assertEqual(order.x_receipt_status, "partial")

        backorder = order.picking_ids.filtered(lambda picking: picking.state != "done")
        self._receive_with_backorder(backorder, {self.product_a: 6.0})
        self.assertEqual(order.order_line.qty_received, 10.0)
        self.assertEqual(order.x_receipt_status, "full")

    def test_receipt_status_multiple_products(self):
        order = self._create_order(
            [(self.product_a, 10.0), (self.product_b, 20.0)]
        )
        order.button_confirm()

        self._receive_with_backorder(
            order.picking_ids,
            {self.product_a: 10.0, self.product_b: 5.0},
        )
        self.assertEqual(order.x_receipt_status, "partial")

        backorder = order.picking_ids.filtered(lambda picking: picking.state != "done")
        self._receive_with_backorder(backorder, {self.product_b: 15.0})
        self.assertEqual(order.x_receipt_status, "full")

    def test_receipt_status_ignores_display_and_service_lines(self):
        order = self._create_order([(self.service, 2.0)])
        order.write(
            {
                "order_line": [
                    Command.create(
                        {
                            "display_type": "line_section",
                            "name": "Section",
                            "product_qty": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "display_type": "line_note",
                            "name": "Note",
                            "product_qty": 0.0,
                        }
                    ),
                ]
            }
        )
        self.assertEqual(order.x_receipt_status, "not_received")

    def test_receipt_status_uses_uom_rounding(self):
        order = self._create_order([(self.product_a, 10.0)])
        order.button_confirm()
        self._receive_with_backorder(order.picking_ids, {self.product_a: 9.996})
        self.assertEqual(order.x_receipt_status, "full")

    def test_receipt_status_follows_returned_quantity(self):
        order = self._create_order([(self.product_a, 10.0)])
        order.button_confirm()
        receipt = order.picking_ids
        self._receive_with_backorder(receipt, {self.product_a: 10.0})
        self.assertEqual(order.x_receipt_status, "full")

        return_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=receipt.ids,
                active_id=receipt.id,
                active_model="stock.picking",
            )
        )
        return_wizard = return_form.save()
        return_wizard.product_return_moves.quantity = 4.0
        return_action = return_wizard.action_create_returns()
        return_picking = self.env["stock.picking"].browse(return_action["res_id"])
        return_picking.action_assign()
        return_picking.move_ids.quantity = 4.0
        return_picking.move_ids.picked = True
        return_picking._action_done()

        self.assertEqual(order.order_line.qty_received, 6.0)
        self.assertEqual(order.x_receipt_status, "partial")

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase


class TestRepairStockOutput(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.production_location = cls.warehouse.repair_type_id.default_location_dest_id
        cls.output_product = cls.env["product.product"].create(
            {
                "name": "Repair Output Product",
                "is_storable": True,
            }
        )
        cls.component = cls.env["product.product"].create(
            {
                "name": "Repair Output Component",
                "is_storable": True,
            }
        )

    def _update_stock(self, product, quantity, lot=None):
        self.env["stock.quant"]._update_available_quantity(
            product,
            self.stock_location,
            quantity,
            lot_id=lot,
        )

    def _quantity(self, product, lot=None):
        return self.env["stock.quant"]._get_available_quantity(
            product,
            self.stock_location,
            lot_id=lot,
        )

    def _create_repair(
        self,
        *,
        product=None,
        quantity=1.0,
        output=True,
        component_quantity=0.0,
        lot=None,
    ):
        product = product or self.output_product
        values = {
            "product_id": product.id,
            "product_qty": quantity,
            "product_uom": product.uom_id.id,
            "picking_type_id": self.warehouse.repair_type_id.id,
            "use_repair_stock_output": output,
        }
        if lot:
            values["lot_id"] = lot.id
        if component_quantity:
            values["move_ids"] = [
                Command.create(
                    {
                        "product_id": self.component.id,
                        "product_uom_qty": component_quantity,
                        "repair_line_type": "add",
                    }
                )
            ]
        return self.env["repair.order"].create(values)

    def _complete_repair(self, repair):
        self.assertTrue(repair.action_validate())
        self.assertEqual(repair.state, "confirmed")
        repair.action_repair_start()
        repair.action_repair_end()
        self.assertEqual(repair.state, "done")

    def _assert_output_move(self, repair, quantity):
        self.assertEqual(repair.move_id.location_id, self.production_location)
        self.assertEqual(repair.move_id.location_dest_id, self.stock_location)
        self.assertEqual(repair.move_id.quantity, quantity)
        self.assertEqual(repair.move_id.state, "done")
        self.assertRecordValues(
            repair.move_id.move_line_ids,
            [
                {
                    "location_id": self.production_location.id,
                    "location_dest_id": self.stock_location.id,
                    "quantity": quantity,
                }
            ],
        )

    def test_standard_mode_keeps_insufficient_quantity_warning(self):
        repair = self._create_repair(output=False)

        result = repair.action_validate()

        self.assertEqual(result["res_model"], "stock.warn.insufficient.qty.repair")
        self.assertEqual(repair.state, "draft")

    def test_output_from_zero_stock(self):
        repair = self._create_repair()

        self._complete_repair(repair)

        self.assertEqual(self._quantity(self.output_product), 1.0)
        self._assert_output_move(repair, 1.0)

    def test_output_adds_to_existing_stock(self):
        self._update_stock(self.output_product, 10.0)
        repair = self._create_repair()

        self._complete_repair(repair)

        self.assertEqual(self._quantity(self.output_product), 11.0)
        self._assert_output_move(repair, 1.0)

    def test_component_is_consumed_once(self):
        self._update_stock(self.component, 10.0)
        repair = self._create_repair(component_quantity=2.0)

        self.assertTrue(repair.action_validate())
        self.assertEqual(repair.move_ids.state, "assigned")
        repair.action_repair_start()
        repair.action_repair_end()

        self.assertEqual(self._quantity(self.output_product), 1.0)
        self.assertEqual(self._quantity(self.component), 8.0)
        self.assertEqual(len(repair.move_ids), 1)
        self.assertEqual(repair.move_ids.location_id, self.stock_location)
        self.assertEqual(repair.move_ids.location_dest_id, self.production_location)
        self.assertEqual(repair.move_ids.quantity, 2.0)

    def test_component_shortage_keeps_standard_availability(self):
        self._update_stock(self.component, 1.0)
        repair = self._create_repair(component_quantity=2.0)

        self.assertTrue(repair.action_validate())

        self.assertEqual(repair.state, "confirmed")
        self.assertEqual(repair.move_ids.state, "partially_available")
        self.assertEqual(repair.move_ids.quantity, 1.0)
        self.assertFalse(repair.is_parts_available)
        self.assertEqual(repair.parts_availability_state, "late")

    def test_actual_component_quantity_uses_standard_move(self):
        self._update_stock(self.component, 10.0)
        repair = self._create_repair(component_quantity=10.0)
        repair.action_validate()
        repair.action_repair_start()
        repair.move_ids.quantity = 8.0

        repair.action_repair_end()

        self.assertEqual(self._quantity(self.component), 2.0)
        self.assertEqual(repair.move_ids.quantity, 8.0)
        self.assertEqual(len(repair.move_ids), 1)

    def test_multiple_output_quantity(self):
        repair = self._create_repair(quantity=5.0)

        self._complete_repair(repair)

        self.assertEqual(self._quantity(self.output_product), 5.0)
        self._assert_output_move(repair, 5.0)

    def test_lot_tracked_output(self):
        product = self.env["product.product"].create(
            {
                "name": "Lot Tracked Repair Output",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        lot = self.env["stock.lot"].create(
            {"name": "LOT/OUTPUT/001", "product_id": product.id}
        )
        repair = self._create_repair(product=product, quantity=10.0, lot=lot)

        self._complete_repair(repair)

        self.assertEqual(self._quantity(product, lot), 10.0)
        self.assertEqual(repair.move_id.move_line_ids.lot_id, lot)
        self._assert_output_move(repair, 10.0)

    def test_serial_tracked_output(self):
        product = self.env["product.product"].create(
            {
                "name": "Serial Tracked Repair Output",
                "is_storable": True,
                "tracking": "serial",
            }
        )
        serial = self.env["stock.lot"].create(
            {"name": "SN/OUTPUT/001", "product_id": product.id}
        )
        repair = self._create_repair(product=product, lot=serial)

        self._complete_repair(repair)

        self.assertEqual(self._quantity(product, serial), 1.0)
        self.assertEqual(repair.move_id.move_line_ids.lot_id, serial)
        self._assert_output_move(repair, 1.0)

    def test_serial_quantity_constraint_is_preserved(self):
        product = self.env["product.product"].create(
            {
                "name": "Invalid Serial Repair Output",
                "is_storable": True,
                "tracking": "serial",
            }
        )
        serial = self.env["stock.lot"].create(
            {"name": "SN/OUTPUT/INVALID", "product_id": product.id}
        )
        repair = self._create_repair(product=product, quantity=2.0, lot=serial)
        repair.action_validate()
        repair.action_repair_start()

        with self.assertRaises(ValidationError):
            repair.action_repair_end()

    def test_end_and_done_are_idempotent(self):
        repair = self._create_repair()
        self._complete_repair(repair)
        move = repair.move_id

        with self.assertRaises(UserError):
            repair.action_repair_end()
        self.assertTrue(repair.action_repair_done())

        self.assertEqual(self._quantity(self.output_product), 1.0)
        self.assertEqual(repair.move_id, move)
        self.assertEqual(
            self.env["stock.move"].search_count(
                [
                    ("repair_id", "=", repair.id),
                    ("repair_line_type", "=", False),
                ]
            ),
            1,
        )

    def test_checkbox_is_locked_after_confirmation(self):
        repair = self._create_repair()
        repair.action_validate()

        with self.assertRaises(UserError):
            repair.use_repair_stock_output = False

    def test_mixed_standard_and_output_recordset(self):
        self._update_stock(self.output_product, 1.0)
        standard_repair = self._create_repair(output=False)
        output_repair = self._create_repair()
        standard_repair.action_validate()
        output_repair.action_validate()
        standard_repair.action_repair_start()
        output_repair.action_repair_start()

        (standard_repair | output_repair).action_repair_done()

        self.assertEqual(standard_repair.state, "done")
        self.assertEqual(output_repair.state, "done")
        self.assertEqual(
            standard_repair.move_id.location_id,
            standard_repair.product_location_src_id,
        )
        self.assertEqual(output_repair.move_id.location_id, self.production_location)
        self.assertEqual(self._quantity(self.output_product), 2.0)

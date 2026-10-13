from odoo import Command, fields
from odoo.tests import TransactionCase


class TestReorderingNotification(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.notification_group = cls.env.ref(
            "stock_reordering_popup_notification.group_reordering_popup_notification"
        )
        cls.stock_manager_group = cls.env.ref("stock.group_stock_manager")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )

    def _create_user(self, login, groups, companies=None):
        companies = companies or self.env.company
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": login,
                "login": login,
                "email": "%s@example.com" % login,
                "company_id": companies[0].id,
                "company_ids": [Command.set(companies.ids)],
                "groups_id": [Command.set(groups.ids)],
            }
        )

    def _create_orderpoint(self, name, quantity=10.0, company=None, warehouse=None):
        company = company or self.env.company
        warehouse = warehouse or self.warehouse
        product = self.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
            }
        )
        return self.env["stock.warehouse.orderpoint"].create(
            {
                "name": "OP %s" % name,
                "product_id": product.id,
                "warehouse_id": warehouse.id,
                "location_id": warehouse.lot_stock_id.id,
                "company_id": company.id,
                "trigger": "manual",
                "product_min_qty": 10.0 if quantity else 0.0,
                "product_max_qty": 50.0 if quantity else 0.0,
                "qty_to_order_manual": quantity,
            }
        )

    def _get_data(self, user, companies=None):
        companies = companies or user.company_ids
        return self.env["stock.warehouse.orderpoint"].with_user(user).with_context(
            allowed_company_ids=companies.ids
        ).get_reordering_notification_data()

    def test_unauthorized_user_receives_no_data(self):
        self._create_orderpoint("Restricted Product", 48.0)
        user = self._create_user("no_notification", self.env.ref("base.group_user"))

        data = self._get_data(user)

        self.assertFalse(data["show"])
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["items"], [])

    def test_authorized_user_without_stock_access_receives_data(self):
        orderpoint = self._create_orderpoint("Paper A4", 48.0)
        user = self._create_user("notification_only", self.notification_group)
        write_date_before = orderpoint.write_date

        data = self._get_data(user)
        orderpoint.invalidate_recordset(["write_date"])

        self.assertTrue(data["show"])
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["product_id"], orderpoint.product_id.id)
        self.assertEqual(data["items"][0]["orderpoint_id"], orderpoint.id)
        self.assertEqual(data["items"][0]["qty_to_order"], 48.0)
        self.assertEqual(
            data["quantity_precision"],
            self.env["decimal.precision"].precision_get("Product Unit of Measure"),
        )
        self.assertFalse(data["can_open_replenishment"])
        self.assertFalse(data["replenishment_action"])
        self.assertFalse(data["can_open_purchase_order"])
        self.assertFalse(data["purchase_order_action"])
        self.assertFalse(data["can_open_purchase_request"])
        self.assertFalse(data["purchase_request_action"])
        self.assertEqual(orderpoint.write_date, write_date_before)

    def test_no_popup_without_quantity_to_order(self):
        self._create_orderpoint("Enough Stock", 0.0)
        user = self._create_user("no_reorder", self.notification_group)

        data = self._get_data(user)

        self.assertFalse(data["show"])
        self.assertEqual(data["total"], 0)

    def test_future_snoozed_orderpoint_is_not_shown(self):
        orderpoint = self._create_orderpoint("Snoozed Product", 10.0)
        orderpoint.snoozed_until = fields.Date.add(fields.Date.today(), days=1)
        user = self._create_user("snoozed_notification", self.notification_group)

        data = self._get_data(user)

        self.assertFalse(data["show"])
        self.assertEqual(data["total"], 0)

    def test_details_are_limited(self):
        for index in range(100):
            self._create_orderpoint("Limited Product %s" % index, index + 1.0)
        user = self._create_user("limited_notification", self.notification_group)

        data = self._get_data(user)

        self.assertEqual(data["total"], 100)
        self.assertEqual(data["limit"], 20)
        self.assertEqual(len(data["items"]), 20)

    def test_only_active_allowed_companies_are_returned(self):
        self._create_orderpoint("Company A Product", 10.0)
        company_b = self.env["res.company"].create({"name": "Notification Company B"})
        warehouse_b = self.env["stock.warehouse"].create(
            {
                "name": "Notification Warehouse B",
                "code": "NWB",
                "company_id": company_b.id,
            }
        )
        self._create_orderpoint(
            "Company B Product",
            20.0,
            company=company_b,
            warehouse=warehouse_b,
        )
        user = self._create_user(
            "company_notification",
            self.notification_group,
            self.env.company | company_b,
        )

        data = self._get_data(user, self.env.company)

        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["product_name"], "Company A Product")

    def test_stock_manager_can_open_standard_action(self):
        self._create_orderpoint("Manager Product", 10.0)
        user = self._create_user(
            "notification_manager",
            self.notification_group | self.stock_manager_group,
        )

        data = self._get_data(user)

        self.assertTrue(data["can_open_replenishment"])
        self.assertEqual(
            data["replenishment_action"], "stock.action_orderpoint_replenish"
        )
        self.assertTrue(self.env.ref(data["replenishment_action"]).exists())

    def test_optional_purchase_actions_follow_user_access(self):
        purchase_action = self.env.ref(
            "purchase.purchase_form_action", raise_if_not_found=False
        )
        purchase_group = self.env.ref(
            "purchase.group_purchase_user", raise_if_not_found=False
        )
        request_action = self.env.ref(
            "purchase_request.purchase_request_form_action", raise_if_not_found=False
        )
        request_group = self.env.ref(
            "purchase_request.group_purchase_request_user", raise_if_not_found=False
        )
        if not all((purchase_action, purchase_group, request_action, request_group)):
            self.skipTest("Optional Purchase and Purchase Request modules are not installed")

        self._create_orderpoint("Purchase Navigation Product", 10.0)
        user = self._create_user(
            "notification_purchase_navigation",
            self.notification_group | purchase_group | request_group,
        )

        data = self._get_data(user)

        self.assertTrue(data["can_open_purchase_order"])
        self.assertEqual(data["purchase_order_action"], "purchase.purchase_form_action")
        self.assertTrue(data["can_open_purchase_request"])
        self.assertEqual(
            data["purchase_request_action"],
            "purchase_request.purchase_request_form_action",
        )

    def test_backend_asset_bundle_builds(self):
        asset_nodes = self.env["ir.qweb"]._get_asset_nodes("web.assets_backend")
        css_bundle = self.env["ir.qweb"]._get_asset_bundle(
            "web.assets_backend", css=True, js=False
        )
        css_attachment = css_bundle.css()

        self.assertTrue(asset_nodes)
        self.assertTrue(css_attachment)
        self.assertFalse(css_bundle.css_errors)

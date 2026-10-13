import logging

from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    @api.model
    def get_reordering_notification_data(self):
        empty_result = {
            "show": False,
            "total": 0,
            "limit": 20,
            "items": [],
            "quantity_precision": 2,
            "can_open_replenishment": False,
            "replenishment_action": False,
            "can_open_purchase_order": False,
            "purchase_order_action": False,
            "can_open_purchase_request": False,
            "purchase_request_action": False,
        }
        user = self.env.user
        if not user.has_group(
            "stock_reordering_popup_notification.group_reordering_popup_notification"
        ):
            return empty_result

        company_ids = self.env.companies.ids
        if not company_ids:
            return empty_result

        limit = empty_result["limit"]
        quantity_precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        orderpoints = self.sudo().with_context(
            allowed_company_ids=company_ids,
        ).search(
            [
                ("active", "=", True),
                ("company_id", "in", company_ids),
                "|",
                ("snoozed_until", "=", False),
                ("snoozed_until", "<=", fields.Date.today()),
            ],
            order="company_id, location_id, product_id, id",
        )

        # qty_to_order is non-stored. Reading it on one recordset lets Odoo
        # compute forecasts in batches instead of issuing one query per product.
        orderpoints.mapped("qty_to_order")
        to_reorder = orderpoints.filtered(lambda orderpoint: orderpoint.qty_to_order > 0.0)
        total = len(to_reorder)
        if not total:
            return empty_result

        items = []
        for orderpoint in to_reorder[:limit]:
            items.append(
                {
                    "orderpoint_id": orderpoint.id,
                    "product_id": orderpoint.product_id.id,
                    "product_name": orderpoint.product_id.display_name,
                    "location_name": orderpoint.location_id.display_name,
                    "warehouse_name": orderpoint.warehouse_id.display_name,
                    "forecast_qty": orderpoint.qty_forecast,
                    "min_qty": orderpoint.product_min_qty,
                    "max_qty": orderpoint.product_max_qty,
                    "qty_to_order": orderpoint.qty_to_order,
                    "uom_name": orderpoint.product_uom_name,
                }
            )

        can_open_replenishment = user.has_group("stock.group_stock_manager")
        purchase_order_action = self.env.ref(
            "purchase.purchase_form_action", raise_if_not_found=False
        )
        purchase_order_group = self.env.ref(
            "purchase.group_purchase_user", raise_if_not_found=False
        )
        can_open_purchase_order = bool(
            purchase_order_action
            and purchase_order_group
            and user.has_group("purchase.group_purchase_user")
        )
        purchase_request_action = self.env.ref(
            "purchase_request.purchase_request_form_action", raise_if_not_found=False
        )
        purchase_request_group = self.env.ref(
            "purchase_request.group_purchase_request_user", raise_if_not_found=False
        )
        can_open_purchase_request = bool(
            purchase_request_action
            and purchase_request_group
            and user.has_group("purchase_request.group_purchase_request_user")
        )
        _logger.debug(
            "Prepared %s reordering rule notifications for user %s in companies %s",
            total,
            user.id,
            company_ids,
        )
        return {
            "show": True,
            "total": total,
            "limit": limit,
            "items": items,
            "quantity_precision": quantity_precision,
            "can_open_replenishment": can_open_replenishment,
            "replenishment_action": (
                "stock.action_orderpoint_replenish" if can_open_replenishment else False
            ),
            "can_open_purchase_order": can_open_purchase_order,
            "purchase_order_action": (
                "purchase.purchase_form_action" if can_open_purchase_order else False
            ),
            "can_open_purchase_request": can_open_purchase_request,
            "purchase_request_action": (
                "purchase_request.purchase_request_form_action"
                if can_open_purchase_request
                else False
            ),
        }

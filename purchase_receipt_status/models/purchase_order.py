from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    x_receipt_status = fields.Selection(
        selection=[
            ("not_received", "Not Received"),
            ("partial", "Partially Received"),
            ("full", "Fully Received"),
        ],
        string="Receipt Status",
        compute="_compute_x_receipt_status",
        store=True,
        readonly=True,
        copy=False,
        index=True,
    )

    @api.depends(
        "order_line.qty_received",
        "order_line.product_qty",
        "order_line.product_uom",
        "order_line.product_uom.rounding",
        "order_line.product_id",
        "order_line.product_id.type",
        "order_line.display_type",
    )
    def _compute_x_receipt_status(self):
        for order in self:
            receipt_lines = order.order_line.filtered(
                lambda line: (
                    not line.display_type
                    and line.product_id
                    and line.product_id.type != "service"
                )
            )

            if not receipt_lines:
                order.x_receipt_status = "not_received"
                continue

            has_received = False
            is_fully_received = True
            for line in receipt_lines:
                rounding = line.product_uom.rounding if line.product_uom else 0.01
                if float_compare(
                    line.qty_received,
                    0.0,
                    precision_rounding=rounding,
                ) > 0:
                    has_received = True
                if float_compare(
                    line.qty_received,
                    line.product_qty,
                    precision_rounding=rounding,
                ) < 0:
                    is_fully_received = False

            if not has_received:
                order.x_receipt_status = "not_received"
            elif is_fully_received:
                order.x_receipt_status = "full"
            else:
                order.x_receipt_status = "partial"

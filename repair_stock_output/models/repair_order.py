from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare


FINAL_MOVE_OUTPUT_CONTEXT = "repair_stock_output_final_move"


class RepairOrder(models.Model):
    _inherit = "repair.order"

    use_repair_stock_output = fields.Boolean(
        string="Produce Repaired Product",
        default=False,
        copy=False,
        help=(
            "Jika aktif, Product to Repair diperlakukan sebagai hasil/output Repair. "
            "Product tidak harus tersedia di stok sebelum Repair dan quantity akan "
            "ditambahkan ke stock ketika Repair selesai."
        ),
    )

    consumed_component_value = fields.Monetary(
        string="Consumed Component Value",
        compute="_compute_repair_valuation_info",
        currency_field="company_currency_id",
        readonly=True,
    )
    output_valuation_value = fields.Monetary(
        string="Output Valuation Value",
        compute="_compute_repair_valuation_info",
        currency_field="company_currency_id",
        readonly=True,
    )
    valuation_difference = fields.Monetary(
        string="Valuation Difference",
        compute="_compute_repair_valuation_info",
        currency_field="company_currency_id",
        readonly=True,
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    def write(self, vals):
        if "use_repair_stock_output" in vals:
            locked_repairs = self.filtered(
                lambda repair: repair.state != "draft"
                and repair.use_repair_stock_output
                != bool(vals["use_repair_stock_output"])
            )
            if locked_repairs:
                raise UserError(
                    _("Produce Repaired Product can only be changed on a draft repair order.")
                )
        return super().write(vals)

    def action_validate(self):
        self.ensure_one()
        if not self.use_repair_stock_output:
            return super().action_validate()

        if any(move.product_uom_qty < 0 for move in self.move_ids):
            raise UserError(_("You can not enter negative quantities."))
        return self._action_repair_confirm()

    def action_repair_done(self):
        output_repairs = self.filtered("use_repair_stock_output")
        if not output_repairs:
            return super().action_repair_done()

        standard_repairs = self - output_repairs
        if standard_repairs:
            super(RepairOrder, standard_repairs).action_repair_done()

        completed_repairs = output_repairs.filtered(
            lambda repair: repair.state == "done"
            or (repair.move_id and repair.move_id.state == "done")
        )
        repairs_with_existing_move = (output_repairs - completed_repairs).filtered(
            "move_id"
        )
        if repairs_with_existing_move:
            raise UserError(
                _(
                    "The final product move already exists for repair order(s): %(repairs)s",
                    repairs=", ".join(repairs_with_existing_move.mapped("name")),
                )
            )

        repairs_to_complete = output_repairs - completed_repairs
        if repairs_to_complete:
            repairs_to_complete._action_repair_done_output()
        return True

    def _get_repair_consumed_moves(self):
        self.ensure_one()
        return self.move_ids.filtered(
            lambda m: m.repair_line_type == "add" and m.state == "done"
        )

    def _get_repair_consumed_value(self):
        """Return absolute total value of consumed components from SVLs."""
        self.ensure_one()
        consumed_moves = self._get_repair_consumed_moves()
        if not consumed_moves:
            return 0.0
        svls = consumed_moves.sudo().stock_valuation_layer_ids
        if not svls:
            return 0.0
        return abs(sum(svls.mapped("value")))

    @api.depends(
        "state",
        "move_ids.state",
        "move_ids.stock_valuation_layer_ids.value",
        "move_id.state",
        "move_id.stock_valuation_layer_ids.value",
        "product_qty",
    )
    def _compute_repair_valuation_info(self):
        for repair in self:
            consumed_value = repair._get_repair_consumed_value()
            output_value = 0.0
            if repair.move_id and repair.move_id.state == "done":
                output_svls = repair.move_id.sudo().stock_valuation_layer_ids
                if output_svls:
                    output_value = abs(sum(output_svls.mapped("value")))
            repair.consumed_component_value = consumed_value
            repair.output_valuation_value = output_value
            repair.valuation_difference = consumed_value - output_value

    def _action_repair_done_output(self):
        """Complete repair orders with use_repair_stock_output=True.

        Flow:
        1. Complete component moves (type 'add') first to generate SVLs
        2. Flush + invalidate cache so SVLs are visible
        3. Read actual consumed component value from SVLs
        4. Calculate output unit cost = total consumed value / output qty
        5. Create final product move with the calculated price_unit
        6. Complete final product move (price_unit flows into SVL)
        7. Set traceability (consume_line_ids) on move lines
        """
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )

        component_moves = self.move_ids.filtered(
            lambda m: m.repair_line_type == "add"
            and m.state not in ("done", "cancel")
        )
        if component_moves:
            component_moves.write({"picked": True})
            component_moves._action_done(cancel_backorder=True)

        self.env.cr.flush()
        self.invalidate_cache()

        total_component_value = self._get_repair_consumed_value()

        output_qty = self.product_qty
        if float_is_zero(output_qty, precision_rounding=self.product_uom.rounding):
            output_unit_cost = 0.0
        else:
            output_unit_cost = total_component_value / output_qty

        if not self.product_id:
            self.write({"state": "done"})
            return True

        if self.product_id.product_tmpl_id.tracking != "none" and not self.lot_id:
            raise UserError(
                _(
                    "Serial number is required for product to repair : %s",
                    self.product_id.display_name,
                )
            )

        owner_id = False
        available_qty_owner = self.env["stock.quant"]._get_available_quantity(
            self.product_id,
            self.location_id,
            self.lot_id,
            owner_id=self.partner_id,
            strict=True,
        )
        if float_compare(
            available_qty_owner, self.product_qty, precision_digits=precision
        ) >= 0:
            owner_id = self.partner_id.id

        source_id = self.location_dest_id.id
        destination_id = self.product_location_dest_id.id

        consumed_move_lines = self.move_ids.filtered(
            lambda m: m.repair_line_type == "add" and m.state == "done"
        ).mapped("move_line_ids")

        product_move_vals = {
            "name": self.name,
            "product_id": self.product_id.id,
            "product_uom": self.product_uom.id or self.product_id.uom_id.id,
            "product_uom_qty": self.product_qty,
            "price_unit": output_unit_cost,
            "partner_id": self.partner_id.id,
            "location_id": source_id,
            "location_dest_id": destination_id,
            "picked": True,
            "picking_id": False,
            "repair_id": self.id,
            "origin": self.name,
            "company_id": self.company_id.id,
            "move_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product_id.id,
                        "lot_id": self.lot_id.id,
                        "product_uom_id": self.product_uom.id
                        or self.product_id.uom_id.id,
                        "quantity": self.product_qty,
                        "package_id": False,
                        "result_package_id": False,
                        "owner_id": owner_id,
                        "location_id": source_id,
                        "company_id": self.company_id.id,
                        "location_dest_id": destination_id,
                        "consume_line_ids": [(6, 0, consumed_move_lines.ids)],
                    },
                )
            ],
        }

        product_move = self.env["stock.move"].with_context(
            **{FINAL_MOVE_OUTPUT_CONTEXT: True}
        ).create(product_move_vals)
        self.move_id = product_move

        product_move._action_done(cancel_backorder=True)

        self.env.cr.flush()
        self.invalidate_cache()

        if consumed_move_lines:
            product_move.move_line_ids.write(
                {"consume_line_ids": [(6, 0, consumed_move_lines.ids)]}
            )

        if self.sale_order_line_id:
            ro_origin_product = self.sale_order_line_id.product_template_id
            no_service_policy = "service_policy" not in self.env["product.template"]
            if ro_origin_product.type == "service" and (
                no_service_policy
                or ro_origin_product.service_policy == "ordered_prepaid"
            ):
                self.sale_order_line_id.qty_delivered = (
                    self.sale_order_line_id.product_uom_qty
                )

        self.write({"state": "done"})
        return True
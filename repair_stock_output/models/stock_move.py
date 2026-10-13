from odoo import api, fields, models
from odoo.fields import Command


from .repair_order import FINAL_MOVE_OUTPUT_CONTEXT


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get(FINAL_MOVE_OUTPUT_CONTEXT):
            for vals in vals_list:
                repair_id = vals.get("repair_id")
                if not repair_id or vals.get("repair_line_type"):
                    continue
                repair = self.env["repair.order"].browse(repair_id).exists()
                if not repair or not repair.use_repair_stock_output:
                    continue

                source_id = repair.location_dest_id.id
                destination_id = repair.product_location_dest_id.id
                vals.update(
                    {
                        "location_id": source_id,
                        "location_dest_id": destination_id,
                    }
                )
                for command in vals.get("move_line_ids", []):
                    if command[0] == Command.CREATE:
                        command[2].update(
                            {
                                "location_id": source_id,
                                "location_dest_id": destination_id,
                            }
                        )
        return super().create(vals_list)
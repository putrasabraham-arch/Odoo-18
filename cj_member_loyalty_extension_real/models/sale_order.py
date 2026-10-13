# -*- coding: utf-8 -*-
import math

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _program_check_compute_points(self, programs):
        """Add an opt-in floor rule: when a loyalty rule has
        `points_per_unit > 0`, recompute its money-mode contribution with
        `floor(amount_paid / points_per_unit)`. Rules without this field
        keep the standard Odoo formula (returned unchanged by super()).
        """
        result = super()._program_check_compute_points(programs)
        for program, program_result in result.items():
            if 'error' in program_result or 'points' not in program_result:
                continue
            points_list = program_result['points']
            if not points_list:
                continue
            head, *rule_points = points_list
            program_result['points'] = [
                self._cja_recompute_program_points(program, head)
            ] + rule_points
        return result

    def _cja_recompute_program_points(self, program, fallback_points):
        self.ensure_one()
        per_unit_rules = program.rule_ids.filtered(
            lambda r: r.reward_point_mode == 'money' and r.points_per_unit > 0
        )
        if not per_unit_rules:
            return fallback_points
        total = 0.0
        used = False
        for rule in per_unit_rules:
            amount = self._cja_amount_paid_for_rule(rule)
            if not amount:
                continue
            total += math.floor(amount / rule.points_per_unit)
            used = True
        return total if used else fallback_points

    def _cja_amount_paid_for_rule(self, rule):
        self.ensure_one()
        valid_products = rule.program_id._get_valid_products(
            self.order_line.product_id
        ).get(rule, self.env['product.product'])
        amount = 0.0
        for line in self.order_line:
            if line.combo_item_id or line.is_reward_line:
                continue
            if line.reward_id.program_id.program_type in (
                'ewallet', 'gift_card', rule.program_id.program_type,
            ):
                continue
            if line.product_id in valid_products:
                amount += self._get_order_line_price(line, 'price_total')
        return amount
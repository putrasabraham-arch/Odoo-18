# -*- coding: utf-8 -*-
from odoo import fields, models


class LoyaltyRule(models.Model):
    _inherit = 'loyalty.rule'

    points_per_unit = fields.Monetary(
        string='Currency per 1 Point',
        currency_field='currency_id',
        default=0.0,
        help="Optional. When set (> 0), the points for this rule are "
             "computed as floor(amount_paid / points_per_unit). "
             "Example: 100000 means Rp 100.000 = 1 point, Rp 350.000 = "
             "3 points (floor). Leave at 0 to keep the standard Odoo "
             "reward_point_amount formula.",
    )
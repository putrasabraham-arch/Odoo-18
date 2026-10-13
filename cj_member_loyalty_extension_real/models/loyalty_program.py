# -*- coding: utf-8 -*-
from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    hide_points_nominal_on_print = fields.Boolean(
        string='Hide Points Nominal on Print',
        default=False,
        help="Hide the monetary value of points in print reports for "
             "this program. Leave unchecked to keep the standard Odoo "
             "report.",
    )
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certificate = fields.Selection(
        selection_add=[
            ('d1_d2', 'D1-D2'),
            ('d3', 'D3'),
            ('bachelor',),
        ],
        ondelete={
            'd1_d2': 'set null',
            'd3': 'set null',
        },
    )
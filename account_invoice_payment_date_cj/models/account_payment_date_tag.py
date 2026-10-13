# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.misc import format_date


class AccountPaymentDateTag(models.Model):
    _name = 'account.payment.date.tag'
    _description = 'Payment Date Tag'
    _rec_name = 'date'
    _order = 'date'

    date = fields.Date(required=True, index=True)

    _sql_constraints = [
        ('date_unique', 'UNIQUE(date)', 'Date must be unique!'),
    ]

    @api.depends('date')
    def _compute_display_name(self):
        for tag in self:
            tag.display_name = (
                format_date(self.env, tag.date, date_format='dd/MM/yyyy')
                if tag.date else ''
            )
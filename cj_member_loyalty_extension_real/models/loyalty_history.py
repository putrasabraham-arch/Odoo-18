# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class LoyaltyHistory(models.Model):
    _inherit = 'loyalty.history'

    point_history_ids = fields.One2many(
        'loyalty.point.history',
        'loyalty_history_id',
        string='Point History Lines',
    )
    point_history_count = fields.Integer(
        compute='_compute_point_history_count',
    )

    @api.depends('point_history_ids')
    def _compute_point_history_count(self):
        for rec in self:
            rec.point_history_count = len(rec.point_history_ids)

    def _sync_point_history(self):
        """Create a `loyalty.point.history` row for each issued point batch.

        The transaction date defaults to the related sales order date; the
        expiry date is computed automatically (+365 days).
        """
        PointHistory = self.env['loyalty.point.history']
        for rec in self:
            if rec.issued <= 0:
                continue
            if rec.point_history_ids:
                continue
            order = False
            if rec.order_model == 'sale.order' and rec.order_id:
                order = self.env['sale.order'].browse(rec.order_id)
            transaction_date = (
                order and order.date_order and order.date_order.date()
                or rec.create_date.date()
            )
            invoice = order.invoice_ids[:1] if order else False
            PointHistory.create({
                'loyalty_history_id': rec.id,
                'loyalty_card_id': rec.card_id.id,
                'partner_id': rec.card_id.partner_id.id,
                'order_id': order.id if order else False,
                'invoice_id': invoice.id if invoice else False,
                'transaction_date': transaction_date,
                'points': rec.issued,
                'status': 'active',
            })

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_point_history()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'issued' in vals or 'card_id' in vals:
            self._sync_point_history()
        return res

    def action_cancel_payment_late(self):
        """Called by `account.move` when payment > 21 days after invoice.

        Decrements the related loyalty card balance and cancels the
        matching `loyalty.point.history` rows.
        """
        PointHistory = self.env['loyalty.point.history']
        for rec in self.filtered(lambda r: r.issued > 0):
            card = rec.card_id
            if card:
                card.sudo().write({
                    'points': max(0.0, card.points - rec.issued),
                })
            batches = PointHistory.search([
                ('loyalty_history_id', '=', rec.id),
                ('status', '=', 'active'),
            ])
            batches.sudo().write({
                'status': 'cancelled',
                'cancellation_reason': _(
                    'Payment received more than 21 days after invoice date'
                ),
            })
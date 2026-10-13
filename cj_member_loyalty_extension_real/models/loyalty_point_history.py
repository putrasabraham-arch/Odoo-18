# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class LoyaltyPointHistory(models.Model):
    _name = 'loyalty.point.history'
    _description = 'Loyalty Point History (CJA Member)'
    _order = 'transaction_date desc, id desc'
    _rec_name = 'display_name'

    POINT_EXPIRY_DAYS = 365

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True,
    )
    loyalty_card_id = fields.Many2one(
        'loyalty.card',
        string='Loyalty Card',
        ondelete='set null',
        index=True,
    )
    loyalty_history_id = fields.Many2one(
        'loyalty.history',
        string='Source Loyalty History',
        ondelete='cascade',
        index=True,
    )
    order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        ondelete='set null',
        index=True,
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        ondelete='set null',
        index=True,
    )
    transaction_date = fields.Date(
        string='Tanggal Transaksi',
        required=True,
        default=fields.Date.context_today,
        index=True,
    )
    points = fields.Float(
        string='Point Masuk',
        required=True,
        digits=(16, 2),
    )
    expiry_date = fields.Date(
        string='Tanggal Expired',
        compute='_compute_expiry_date',
        store=True,
        index=True,
    )
    status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='active',
        required=True,
        index=True,
    )
    cancellation_reason = fields.Char(string='Cancellation Reason')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )

    _sql_constraints = [
        ('points_non_negative', 'CHECK (points >= 0)', 'Points must be non-negative.'),
    ]

    @api.depends('partner_id', 'transaction_date', 'points')
    def _compute_display_name(self):
        for rec in self:
            partner = rec.partner_id.name or _('Unknown')
            rec.display_name = f"{partner} - {rec.transaction_date} ({int(rec.points)} pts)"

    @api.depends('transaction_date')
    def _compute_expiry_date(self):
        for rec in self:
            if rec.transaction_date:
                rec.expiry_date = rec.transaction_date + relativedelta(
                    days=self.POINT_EXPIRY_DAYS
                )
            else:
                rec.expiry_date = False

    @api.model
    def _cron_expire_points(self):
        """Scheduled action: mark point batches past their expiry_date as
        'expired' and decrement the related loyalty card balance.
        """
        today = fields.Date.context_today(self)
        batches = self.search([
            ('status', '=', 'active'),
            ('expiry_date', '!=', False),
            ('expiry_date', '<', today),
        ])
        if not batches:
            return True
        loyalty_history = self.env['loyalty.history']
        for batch in batches:
            card = batch.loyalty_card_id
            if card and batch.points > 0:
                card.sudo().write({
                    'points': max(0.0, card.points - batch.points),
                })
            batch.write({
                'status': 'expired',
                'cancellation_reason': _('Expired on %s', batch.expiry_date),
            })
            if batch.loyalty_history_id:
                loyalty_history.browse(batch.loyalty_history_id.id).sudo().write({
                    'status': 'expired',
                    'cancellation_reason': _('Points expired on %s', batch.expiry_date),
                })
        return True

    def action_mark_expired(self):
        self.ensure_one()
        if self.status != 'active':
            return True
        card = self.loyalty_card_id
        if card and self.points > 0:
            card.sudo().write({'points': max(0.0, card.points - self.points)})
        self.write({
            'status': 'expired',
            'cancellation_reason': _('Manually expired'),
        })
        if self.loyalty_history_id:
            self.loyalty_history_id.sudo().write({
                'status': 'expired',
                'cancellation_reason': _('Manually expired'),
            })
        return True
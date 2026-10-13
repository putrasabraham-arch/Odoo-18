# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_date_ids = fields.Many2many(
        'account.payment.date.tag',
        string='Tanggal Pembayaran',
        compute='_compute_payment_date_ids',
        help="Tanggal pembayaran yang sudah direkonsiliasi dengan invoice ini. "
             "Satu tag per tanggal unik (duplikat otomatis diabaikan). "
             "Kosong jika invoice belum pernah dibayar.",
    )

    @api.depends('reconciled_payment_ids', 'reconciled_payment_ids.date')
    def _compute_payment_date_ids(self):
        Tag = self.env['account.payment.date.tag']
        for move in self:
            unique_dates = {d for d in move.reconciled_payment_ids.mapped('date') if d}
            tags = Tag.browse()
            for d in sorted(unique_dates):
                # Bypass ACL on the tag model: search/create must always work
                # regardless of the current user's permissions. Tags are an
                # internal implementation detail; users only have read access
                # (see security/ir.model.access.csv). Using sudo() (not
                # with_user(SUPERUSER_ID)) is required because Odoo 18's
                # with_user() always forces su=False.
                Tag_sudo = Tag.sudo()
                tag = Tag_sudo.search([('date', '=', d)], limit=1)
                if not tag:
                    tag = Tag_sudo.create({'date': d})
                tags |= tag
            move.payment_date_ids = tags
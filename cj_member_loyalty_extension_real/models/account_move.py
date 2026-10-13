# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    PAYMENT_WINDOW_DAYS = 21

    def write(self, vals):
        res = super().write(vals)
        if 'payment_state' in vals and not self.env.context.get(
            'skip_cja_payment_check'
        ):
            paid = self.filtered(
                lambda m: m.move_type == 'out_invoice'
                and m.payment_state == 'paid'
            )
            if paid:
                paid._cja_check_payment_window()
        return res

    def _cja_check_payment_window(self):
        """When an invoice becomes fully paid, revoke the related loyalty
        points if the latest payment date is more than 21 days after the
        invoice date.
        """
        History = self.env['loyalty.history']
        for move in self:
            if not move.invoice_date:
                continue
            latest_payment_date = max(
                (p.date for p in move.reconciled_payment_ids if p.date),
                default=False,
            )
            if not latest_payment_date:
                continue
            days_late = (latest_payment_date - move.invoice_date).days
            if days_late <= self.PAYMENT_WINDOW_DAYS:
                continue
            history_lines = History.search([
                ('order_model', '=', 'sale.order'),
                ('order_id', 'in',
                 move.invoice_line_ids.sale_line_ids.order_id.ids),
                ('issued', '>', 0),
            ])
            if history_lines:
                history_lines.action_cancel_payment_late()
        return True
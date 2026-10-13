# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    invoice_date = fields.Date(string="Tanggal Faktur", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        # Correlated scalar subquery: for each grouped row of `sale.report`,
        # return the MAX(invoice_date) of every posted customer invoice
        # linked to any sale order line of the same Sale Order (`s.id`,
        # which is in the outer GROUP BY).
        #
        # Why correlate on `s.id` and not `l.id`:
        #   `l.id` is not part of the outer GROUP BY (it is computed as
        #   MIN(l.id)), so PostgreSQL refuses to use it from a correlated
        #   subquery. The order id (`s.id`) IS grouped, so it is safe and
        #   still gives the "latest posted customer invoice date" of the
        #   sale order.
        #
        # Why a scalar correlated subquery (and not a JOIN):
        #   A LEFT JOIN to `sale_order_line_invoice_rel` / `account_move`
        #   would multiply each row by the number of related invoice lines
        #   and would inflate SUM(product_uom_qty), SUM(price_subtotal),
        #   SUM(price_total), ... A scalar subquery is evaluated once per
        #   outer row and never affects the aggregate measures.
        #
        # Behaviour:
        #   - Only posted customer invoices (move_type = 'out_invoice',
        #     state = 'posted') are considered.
        #   - When several invoices exist for the same sale order line,
        #     MAX(invoice_date) is used (the latest invoice date).
        #   - When no posted customer invoice exists yet, the value is
        #     NULL (displayed as an empty cell).
        res['invoice_date'] = """
            (SELECT MAX(am.invoice_date)
               FROM sale_order_line_invoice_rel rel
               JOIN account_move_line aml ON aml.id = rel.invoice_line_id
               JOIN account_move am ON am.id = aml.move_id
              WHERE rel.order_line_id IN (
                  SELECT sol.id
                    FROM sale_order_line sol
                   WHERE sol.order_id = s.id
              )
                AND am.move_type = 'out_invoice'
                AND am.state = 'posted'
            )"""
        return res
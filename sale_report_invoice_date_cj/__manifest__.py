# -*- coding: utf-8 -*-
{
    'name': 'Sale Report Invoice Date (CJ)',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add Tanggal Faktur (invoice date) column on Sales Analysis',
    'description': """
        Add an optional "Tanggal Faktur" column on the Sales Analysis report
        (Sales > Reporting > Sales) that displays, for each sale order line,
        the latest invoice date (MAX(account_move.invoice_date)) of the
        related posted customer invoices.

        The invoice date is resolved via the relation table
        `sale_order_line_invoice_rel`, only for posted customer invoices
        (move_type = 'out_invoice', state = 'posted').

        When several invoices are linked to the same sale order line,
        the latest invoice date is used.

        The field is computed through a correlated subquery in the
        `sale.report` SQL definition, so it does not duplicate any
        aggregated measure (quantity, subtotal, total).

        Features:
            - Optional column on the Sales Analysis list view (after
              "Tanggal Order").
            - Search / filter by Tanggal Faktur.
            - Group By Tanggal Faktur (day / week / month / year).
            - Empty value when no posted invoice is related.

        Does not modify any core Odoo source code.
    """,
    'author': 'CJ',
    'depends': [
        'sale',
        'account',
    ],
    'data': [
        'views/sale_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
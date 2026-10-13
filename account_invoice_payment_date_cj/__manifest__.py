# -*- coding: utf-8 -*-
{
    'name': 'Account Invoice Payment Date (CJ)',
    'version': '18.0.1.1.0',
    'category': 'Accounting',
    'summary': 'Optional Tanggal Pembayaran tags on Invoice list + Referensi Pembayaran on Other Info',
    'description': """
        Add an optional "Tanggal Pembayaran" column on the Invoice list view
        (Accounting > Customers > Invoices) that displays every reconciled
        payment date as a tag, deduplicated.

        Also add a readonly "Referensi Pembayaran" field on the Invoice form
        (Other Info > Accounting) that displays every reconciled payment
        reference as a tag.

        Both fields are recomputed automatically when payments are
        reconciled, unreconciled, reversed or cancelled.
        Does not modify any core Odoo source code.
        Does not interfere with invoice posting, payments, reconciliation
        or any other accounting flow.
    """,
    'author': 'CJ',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
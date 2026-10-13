# -*- coding: utf-8 -*-
{
    'name': 'CJ Member Loyalty Extension (Real)',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Member Loyalty CJA: floor point per Rp 100k, 365-day expiry, 21-day payment window',
    'description': """
Extends the standard Odoo 18 Loyalty module **without changing its core
behaviour**.

* **Point tracking** — new `loyalty.point.history` records one row per
  earned point batch with customer, order/invoice, transaction date,
  points, expiry date and status.
* **Per-transaction expiry** — every batch expires 365 days after the
  transaction date.
* **Daily cron** — automatically marks expired batches and decrements
  the related loyalty card balance.
* **21-day payment rule (customer bon)** — when an invoice is paid more
  than 21 days after the invoice date, the related point batch is
  cancelled and points are revoked.
* **Opt-in floor rule** — `loyalty.rule.points_per_unit` lets a rule use
  `floor(amount / points_per_unit)` instead of the standard Odoo formula.
  Default is `0` so the standard Odoo loyalty behaviour is preserved.
* **Opt-in print-report** — `loyalty.program.hide_points_nominal_on_print`
  hides the monetary value of points in the gift-card print report.
  Default is `False` so the standard Odoo report is preserved.

No core Odoo module is modified. All changes use `_inherit`.
    """,
    'author': 'CJ',
    'depends': [
        'loyalty',
        'sale_loyalty',
        'account',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/loyalty_rule_views.xml',
        'views/loyalty_program_views.xml',
        'views/loyalty_history_views.xml',
        'views/loyalty_point_history_views.xml',
        'views/loyalty_point_history_menus.xml',
        'views/loyalty_report_templates.xml',
        'data/cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
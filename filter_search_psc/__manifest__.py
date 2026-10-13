# -*- coding: utf-8 -*-
{
    'name': 'Email Marketing - Manual Partner Recipients (filter_search_psc)',
    'version': '18.0.1.0.0',
    'summary': 'Pilih penerima email marketing secara manual (banyak kontak) atau gunakan filter standar',
    'description': """
Adds a recipient mode selector on Email Marketing (mailing.mailing):
- Filter Standar: default behavior of Odoo Email Marketing (unchanged);
- Pilih Kontak Manual: pick multiple res.partner contacts as recipients
  (search by name, tags display, only partners with email, no creation).
Manual selection is converted into the standard recipient domain
[('id', 'in', partner_ids)] on res.partner, so queueing, blacklist,
unsubscribe, tracking, bounce, test and scheduling all keep using the
standard Email Marketing mechanisms.
""",
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['mass_mailing', 'contacts'],
    'data': [
        'views/mailing_mailing_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
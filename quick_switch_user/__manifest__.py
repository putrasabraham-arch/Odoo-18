# -*- coding: utf-8 -*-
{
    'name': 'Quick Switch User',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Fitur untuk berpindah user dengan cepat',
    'author': 'Custom Dev',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'quick_switch_user/static/src/js/main.js',
        ],
        'web.assets_qweb': [
            'quick_switch_user/static/src/xml/templates.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-
{
    'name': 'App - User Login Lock',
    'summary': 'Lock, unlock and deactivate Odoo user access without archiving users',
    'version': '18.0.1.0.0',
    'category': 'Administration/Security',
    'author': 'Bram',
    'website': 'https://github.com/putrasabraham-arch',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/app_user_login_lock_security.xml',
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/app_user_login_lock_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
}

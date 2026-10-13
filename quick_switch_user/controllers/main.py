# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class QuickSwitchUserController(http.Controller):

    @http.route('/web/switch_user_list', type='json', auth='user')
    def get_users(self):
        """Get list of users to switch to"""
        # Hanya buat admin yang bisa switch
        if not request.env.user.has_group('base.group_system'):
            return {'status': 'error', 'message': 'Not authorized'}

        users = request.env['res.users'].search([
            ('active', '=', True),
            ('id', '!=', request.env.user.id)
        ], order='name')

        return {
            'status': 'ok',
            'users': [{'id': u.id, 'name': u.name} for u in users]
        }

    @http.route('/web/do_switch_user', type='json', auth='user')
    def do_switch(self, user_id):
        """Switch to another user"""
        if not request.env.user.has_group('base.group_system'):
            return {'status': 'error', 'message': 'Not authorized'}

        user = request.env['res.users'].browse(int(user_id))
        
        if not user.exists() or not user.active:
            return {'status': 'error', 'message': 'User tidak ditemukan'}

        # Update session dengan user baru
        request.session.uid = user.id
        request.session.update_context(lang=user.lang, tz=user.tz)
        
        # Ensure session is properly saved to prevent JSON parse errors
        try:
            request.session.save()
        except AttributeError:
            # Fallback for different Odoo versions
            try:
                request.session.flush()
            except AttributeError:
                pass

        return {
            'status': 'ok',
            'message': f'Berhasil switch ke {user.name}'
        }

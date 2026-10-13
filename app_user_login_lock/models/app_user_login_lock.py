# -*- coding: utf-8 -*-
"""Dedicated management model for manual login lock.

Each manageable Odoo user gets one ``app.user.login.lock`` record so managers
can lock/unlock logins and deactivate accounts from a dedicated application
menu instead of editing the user form. The real lock state still lives on
``res.users.login_locked`` so the existing authentication enforcement keeps
working.

Users holding the Login Lock Manager right (and the superuser) are never
listed, cannot be added and can never be managed from this app.
"""
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

MANAGER_GROUP = 'app_user_login_lock.group_app_user_login_lock_manager'


class AppUserLoginLock(models.Model):
    _name = 'app.user.login.lock'
    _description = 'User Login Lock Management'
    _order = 'name'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(
        string='Name',
        related='user_id.name',
        store=True,
        readonly=True,
    )
    login = fields.Char(
        string='Login',
        related='user_id.login',
        store=True,
        readonly=True,
    )
    user_active = fields.Boolean(
        string='Active',
        related='user_id.active',
        store=True,
        readonly=True,
    )
    is_privileged = fields.Boolean(
        string='Is Privileged',
        compute='_compute_is_privileged',
        store=True,
    )
    locked = fields.Boolean(
        string='Login Locked',
        related='user_id.login_locked',
        store=True,
        help='When enabled, this user cannot authenticate to Odoo.',
    )
    locked_by = fields.Many2one(
        'res.users',
        string='Locked By',
        related='user_id.login_locked_by',
        store=True,
        readonly=True,
    )
    locked_at = fields.Datetime(
        string='Locked At',
        related='user_id.login_locked_at',
        store=True,
        readonly=True,
    )

    @api.depends('user_id')
    def _compute_is_privileged(self):
        for rec in self:
            rec.is_privileged = (
                rec.user_id.id == SUPERUSER_ID
                or rec.user_id.sudo().has_group(MANAGER_GROUP)
            )

    @api.constrains('user_id')
    def _check_user_id_not_privileged(self):
        for rec in self:
            if rec.is_privileged:
                raise ValidationError(
                    _('Users with login lock management rights and the superuser '
                      'cannot be managed from this list.'))

    def _check_can_manage(self):
        self.ensure_one()
        user = self.user_id
        if user.id == self.env.uid:
            raise UserError(_('You cannot manage your own account.'))
        if user.id == SUPERUSER_ID:
            raise UserError(_('You cannot manage the Odoo superuser.'))
        if user.sudo().has_group(MANAGER_GROUP):
            raise UserError(_('Users with login lock management rights cannot be managed.'))

    def action_sync_users(self):
        """Reconcile the list with all manageable users."""
        all_users = self.env['res.users'].search([])
        privileged = all_users.filtered(
            lambda u: u.id == SUPERUSER_ID or u.sudo().has_group(MANAGER_GROUP))
        self.search([('user_id', 'in', privileged.ids)]).unlink()
        existing = self.search([]).mapped('user_id')
        missing = all_users - privileged - existing
        if missing:
            self.create([{'user_id': user.id} for user in missing])
        return True

    def action_lock_login(self):
        for rec in self:
            rec._check_can_manage()
            rec.user_id.sudo().with_context(app_lock_actor=self.env.uid).action_lock_login()
        return True

    def action_unlock_login(self):
        for rec in self:
            rec._check_can_manage()
            rec.user_id.sudo().with_context(app_lock_actor=self.env.uid).action_unlock_login()
        return True

    def action_deactivate_user(self):
        for rec in self:
            rec._check_can_manage()
            rec.user_id.sudo().write({'active': False})
        return True

    def action_activate_user(self):
        for rec in self:
            rec._check_can_manage()
            rec.user_id.sudo().write({'active': True})
        return True

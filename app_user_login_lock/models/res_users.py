# -*- coding: utf-8 -*-
"""Manual login lock for Odoo 18 Community.

Uses the native Odoo authentication and session-token extension points instead
of monkey-patching controllers or altering the ``active`` field.
"""
import logging
import uuid

from odoo import SUPERUSER_ID, _, fields, models
from odoo.exceptions import AccessDenied, AccessError, UserError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    login_locked = fields.Boolean(
        string='Login Locked',
        default=False,
        copy=False,
        groups='app_user_login_lock.group_app_user_login_lock_manager',
        help='When enabled, this user cannot authenticate to Odoo.',
    )
    login_lock_version = fields.Char(
        string='Login Lock Session Version',
        default=lambda self: uuid.uuid4().hex,
        copy=False,
        readonly=True,
        groups='app_user_login_lock.group_app_user_login_lock_manager',
        help='Changing this token permanently invalidates older browser sessions.',
    )
    login_locked_by = fields.Many2one(
        'res.users',
        string='Locked By',
        copy=False,
        readonly=True,
        groups='app_user_login_lock.group_app_user_login_lock_manager',
    )
    login_locked_at = fields.Datetime(
        string='Locked At',
        copy=False,
        readonly=True,
        groups='app_user_login_lock.group_app_user_login_lock_manager',
    )

    def _get_session_token_fields(self):
        """Invalidate old sessions whenever an administrator toggles lock.

        A new random version is required: a mere Boolean toggled locked->
        unlocked could otherwise re-validate a session that did not make any
        HTTP request while the user was locked.
        """
        return super()._get_session_token_fields() | {
            'login_locked',
            'login_lock_version',
        }

    def _check_credentials(self, credential, env):
        """Stop password, OAuth and other auth implementations at login time."""
        self.ensure_one()
        if self.sudo().login_locked:
            _logger.warning('Login denied for locked user id=%s', self.id)
            raise AccessDenied(_('Your account has been locked. Contact your administrator.'))
        return super()._check_credentials(credential, env)

    def _assert_login_lock_admin(self):
        if not self.env.user.has_group('app_user_login_lock.group_app_user_login_lock_manager'):
            raise AccessError(_('Only Login Lock Managers can lock or unlock user logins.'))

    def _validate_lock_targets(self):
        """Keep a recoverable Login Lock Manager available."""
        if self.env.uid in self.ids:
            raise UserError(_('You cannot lock your own account.'))
        if SUPERUSER_ID in self.ids:
            raise UserError(_('You cannot lock the Odoo superuser.'))
        if any(user.sudo().has_group('app_user_login_lock.group_app_user_login_lock_manager') for user in self):
            raise UserError(_('Users with login lock management rights cannot be locked.'))

    def write(self, vals):
        if 'login_locked' in vals:
            self._assert_login_lock_admin()
            if vals['login_locked']:
                self._validate_lock_targets()
            # Generate a fresh version for *both* directions, including if an
            # admin repeats an action; sessions issued before the change stay
            # invalid even after unlocking.
            vals = dict(vals)
            # The lock can be toggled through the dedicated app with elevated
            # rights (sudo); keep auditing the real acting user in that case.
            actor = self.env.context.get('app_lock_actor', self.env.uid)
            vals.update({
                'login_lock_version': uuid.uuid4().hex,
                'login_locked_by': actor if vals['login_locked'] else False,
                'login_locked_at': fields.Datetime.now() if vals['login_locked'] else False,
            })
            _logger.info('Login lock changed to %s on user ids=%s by uid=%s',
                         vals['login_locked'], self.ids, actor)
        return super().write(vals)

    def action_lock_login(self):
        self._assert_login_lock_admin()
        self._validate_lock_targets()
        self.write({'login_locked': True})
        return True

    def action_unlock_login(self):
        self._assert_login_lock_admin()
        self.write({'login_locked': False})
        return True

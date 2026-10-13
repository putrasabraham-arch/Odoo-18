# -*- coding: utf-8 -*-
"""Cover HTTP bearer/API key routes in addition to browser login."""
from odoo import models, _
from odoo.exceptions import AccessDenied
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_bearer(cls):
        # Let Odoo authenticate and apply all standard bearer-token checks.
        result = super()._auth_method_bearer()
        # Odoo 18 also allows an interactive session on bearer routes. In that
        # situation the session-token mechanism already invalidates old logins;
        # this additional check covers direct API keys (no browser session).
        if request.env.uid and request.env.user.sudo().login_locked:
            raise AccessDenied(_('Your account has been locked. Contact your administrator.'))
        return result

# -*- coding: utf-8 -*-
from . import models


def post_init_hook(env):
    """Populate one management record per user right after installation."""
    env['app.user.login.lock'].action_sync_users()


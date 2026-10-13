# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request


class SwitchUserWizard(models.TransientModel):
    _name = 'switch.user.wizard'
    _description = 'Switch User Wizard'

    user_id = fields.Many2one(
        'res.users',
        string='Select User',
        required=True,
        domain="[('active', '=', True), ('id', '!=', uid)]"
    )

    def action_switch_user(self):
        """Switch to selected user"""
        self.ensure_one()
        
        # Update session user
        self.env.user = self.user_id
        request.session.uid = self.user_id.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


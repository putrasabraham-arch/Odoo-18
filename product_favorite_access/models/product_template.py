# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import AccessError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _check_star_access(self):
        """Check apakah user memiliki akses ke fitur Star"""
        group_star = self.env.ref('product_favorite_access.group_product_star_access', raise_if_not_found=False)
        if not group_star:
            return False
        return self.env.user in group_star.users
    
    def _check_write_access_on_is_favorite(self):
        """Validate permission sebelum update is_favorite"""
        if not self._check_star_access():
            raise AccessError(
                "Anda tidak memiliki izin untuk mengubah status favorite/star produk. "
                "Hubungi administrator untuk mendapatkan akses 'Akses Star Product'."
            )
    
    def write(self, vals):
        """Override write untuk validate akses is_favorite"""
        # Jika ada field is_favorite yang di-update
        if 'is_favorite' in vals:
            self._check_write_access_on_is_favorite()
        
        return super().write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Prevent user tanpa akses create produk dengan is_favorite=True"""
        for vals in vals_list:
            if vals.get('is_favorite'):
                self._check_write_access_on_is_favorite()
        
        return super().create(vals_list)
    
    @api.constrains('is_favorite')
    def _constraint_is_favorite_access(self):
        """Constraint untuk memastikan hanya user dengan akses bisa set is_favorite"""
        for record in self:
            if record.is_favorite and not self._check_star_access():
                raise AccessError(
                    "Anda tidak memiliki izin untuk menandai produk sebagai favorite. "
                    "Hubungi administrator untuk mendapatkan akses 'Akses Star Product'."
                )

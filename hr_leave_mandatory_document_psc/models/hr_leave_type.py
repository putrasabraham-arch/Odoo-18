from odoo import api, fields, models


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    mandatory_support_document = fields.Boolean(
        string='Wajib Dokumen Pendukung',
        help="Jika diaktifkan, pengajuan cuti dengan tipe ini tidak dapat "
             "disimpan/disetujui sebelum dokumen pendukung dilampirkan.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('mandatory_support_document'):
                vals['support_document'] = True
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('mandatory_support_document'):
            vals['support_document'] = True
        return super().write(vals)
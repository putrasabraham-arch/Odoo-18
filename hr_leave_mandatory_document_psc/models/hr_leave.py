from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    leave_type_mandatory_support_document = fields.Boolean(
        related='holiday_status_id.mandatory_support_document')

    def _check_mandatory_support_document(self):
        # Dokumen pendukung diunggah lewat route terpisah
        # (/web/binary/upload_attachment) yang tidak pernah menulis field
        # hr.leave, sehingga validasi di create()/write() tidak mengganggu
        # proses upload dan tidak menghasilkan error JSON.
        for leave in self.filtered(
                lambda l: l.holiday_status_id.mandatory_support_document):
            if not leave.attachment_ids:
                raise ValidationError(_(
                    "Dokumen pendukung wajib dilampirkan untuk tipe cuti '%s'. "
                    "Silakan lampirkan dokumen terlebih dahulu sebelum "
                    "mengajukan cuti.",
                    leave.holiday_status_id.name,
                ))

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        leaves._check_mandatory_support_document()
        return leaves

    def write(self, vals):
        res = super().write(vals)
        if vals.keys() & {'attachment_ids', 'supported_attachment_ids', 'holiday_status_id'}:
            self._check_mandatory_support_document()
        return res

    def action_approve(self, check_state=True):
        self._check_mandatory_support_document()
        return super().action_approve(check_state=check_state)

    def action_validate(self, check_state=True):
        self._check_mandatory_support_document()
        return super().action_validate(check_state=check_state)
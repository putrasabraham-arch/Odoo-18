# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    recipient_selection = fields.Selection([
        ('domain', 'Filter Standar'),
        ('partner', 'Pilih Kontak Manual'),
    ], string='Metode Penerima', default='domain', copy=True,
        help='Filter Standar: gunakan mekanisme filter/domain standar Email Marketing.\n'
             'Pilih Kontak Manual: pilih beberapa kontak/pelanggan secara manual, '
             'mereka dikonversi menjadi domain recipient res.partner standar.')
    partner_ids = fields.Many2many(
        'res.partner', 'mailing_mailing_partner_recipient_rel',
        'mailing_id', 'partner_id', string='Pelanggan',
        check_company=True, copy=True,
        domain="[('email', '!=', False)]",
        help='Hanya kontak yang memiliki email. Pencarian berdasarkan nama, '
             'bisa memilih lebih dari satu kontak, tanpa membuat kontak baru.')

    # -------------------------------------------------------------------------
    # Recipient model consistency: manual mode always targets res.partner so
    # every standard Email Marketing mechanism keeps working as-is.
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        partner_model = self.env['ir.model']._get('res.partner')
        for vals in vals_list:
            if vals.get('recipient_selection') == 'partner':
                vals['mailing_model_id'] = partner_model.id
        return super().create(vals_list)

    def write(self, vals):
        partner_model = self.env['ir.model']._get('res.partner')
        if vals.get('recipient_selection') == 'partner' and not vals.get('mailing_model_id'):
            vals['mailing_model_id'] = partner_model.id
        res = super().write(vals)
        # Keep the recipient model consistent when the mailing is already in
        # manual mode (e.g. API writes changing the model).
        partner_mailings = self.filtered(
            lambda mailing: mailing.recipient_selection == 'partner'
            and mailing.mailing_model_id != partner_model)
        if partner_mailings:
            partner_mailings.write({'mailing_model_id': partner_model.id})
        return res

    @api.onchange('recipient_selection')
    def _onchange_recipient_selection(self):
        if self.recipient_selection == 'partner':
            self.mailing_model_id = self.env['ir.model']._get('res.partner')
        # Switching back to 'domain' keeps the standard behavior unchanged.

    # -------------------------------------------------------------------------
    # Recipient domain: manual partners are converted to the standard domain
    # [('id', 'in', partner_ids.ids)] on res.partner.
    # -------------------------------------------------------------------------
    @api.depends('mailing_model_id', 'contact_list_ids', 'mailing_type', 'mailing_filter_id',
                 'recipient_selection', 'partner_ids')
    def _compute_mailing_domain(self):
        partner_mailings = self.filtered(
            lambda mailing: mailing.recipient_selection == 'partner')
        super(MailingMailing, self - partner_mailings)._compute_mailing_domain()
        for mailing in partner_mailings:
            partners = mailing.partner_ids.filtered(lambda partner: partner.email)
            if partners:
                mailing.mailing_domain = repr([
                    ('id', 'in', partners.ids),
                    ('email', '!=', False),
                ])
            else:
                mailing.mailing_domain = ''

    def _get_recipients_domain(self):
        """Standard overridable getter used at send time: return the domain
        built from the manually selected partners (only partners with email)."""
        self.ensure_one()
        if self.recipient_selection == 'partner':
            partners = self.partner_ids.filtered(
                lambda partner: (partner.email or '').strip())
            if not partners:
                return [('id', '=', 0)]
            return [('id', 'in', partners.ids), ('email', '!=', False)]
        return super()._get_recipients_domain()

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------
    def _validate_partner_recipients(self):
        for mailing in self:
            if mailing.recipient_selection != 'partner':
                continue
            if not mailing.partner_ids:
                raise ValidationError(_(
                    'Pilih minimal satu kontak pada mode "Pilih Kontak Manual" '
                    'sebelum melakukan Test / Kirim / Jadwalkan.'))
            without_email = mailing.partner_ids.filtered(
                lambda partner: not (partner.email or '').strip())
            if without_email:
                raise ValidationError(_(
                    'Kontak berikut tidak memiliki email dan tidak dapat menjadi penerima: %s'
                ) % ', '.join(without_email.mapped('display_name')))
            # Safety net: manual mode must stay on the standard res.partner
            # recipient model.
            if mailing.mailing_model_real != 'res.partner':
                mailing.mailing_model_id = self.env['ir.model']._get('res.partner')

    def action_test(self):
        self._validate_partner_recipients()
        return super().action_test()

    def action_launch(self):
        self._validate_partner_recipients()
        return super().action_launch()

    def action_schedule(self):
        self._validate_partner_recipients()
        return super().action_schedule()

    def action_put_in_queue(self):
        self._validate_partner_recipients()
        return super().action_put_in_queue()
# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPartnerRecipient(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'PT A', 'email': 'a@example.com'})
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'MMP B', 'email': 'b@example.com'})
        cls.partner_no_email = cls.env['res.partner'].create({
            'name': 'No Email Partner'})

    def test_10_manual_mode_forces_res_partner_model(self):
        mailing = self.env['mailing.mailing'].create({
            'subject': 'Test', 'mailing_type': 'mail',
            'recipient_selection': 'partner',
            'partner_ids': [(6, 0, (self.partner_a + self.partner_b).ids)],
        })
        self.assertEqual(mailing.mailing_model_real, 'res.partner')
        self.assertEqual(len(mailing.partner_ids), 2)
        domain = eval(mailing.mailing_domain)
        self.assertEqual(domain, [
            ('id', 'in', (self.partner_a | self.partner_b).ids),
            ('email', '!=', False)])

    def test_20_recipients_domain(self):
        mailing = self.env['mailing.mailing'].create({
            'subject': 'Test', 'mailing_type': 'mail',
            'recipient_selection': 'partner',
            'partner_ids': [(6, 0, (self.partner_a + self.partner_b).ids)],
        })
        self.assertEqual(
            mailing._get_recipients_domain(),
            [('id', 'in', (self.partner_a | self.partner_b).ids),
             ('email', '!=', False)])
        # partner without email is excluded from the recipient domain
        mailing.partner_ids += self.partner_no_email
        self.assertEqual(
            mailing._get_recipients_domain(),
            [('id', 'in', (self.partner_a | self.partner_b).ids),
             ('email', '!=', False)])

    def test_30_validation(self):
        mailing = self.env['mailing.mailing'].create({
            'subject': 'Test', 'mailing_type': 'mail',
            'recipient_selection': 'partner'})
        with self.assertRaisesRegex(ValidationError, 'minimal satu kontak'):
            mailing.action_put_in_queue()
        mailing.partner_ids += self.partner_no_email
        with self.assertRaisesRegex(ValidationError, 'tidak memiliki email'):
            mailing.action_put_in_queue()
        with self.assertRaisesRegex(ValidationError, 'tidak memiliki email'):
            mailing.action_schedule()

    def test_40_standard_mode_untouched(self):
        mailing = self.env['mailing.mailing'].create({
            'subject': 'Standard', 'mailing_type': 'mail',
            'mailing_model_id': self.env['ir.model']._get('res.partner').id,
        })
        self.assertEqual(mailing.recipient_selection, 'domain')
        self.assertEqual(
            mailing.mailing_domain, repr(mailing._get_default_mailing_domain()))
        self.assertEqual(
            mailing._get_recipients_domain(),
            mailing._parse_mailing_domain())
        mailing.recipient_selection = 'domain'
        mailing.mailing_model_id = self.env['ir.model']._get('res.partner')
        self.assertEqual(
            mailing._get_recipients_domain(),
            mailing._parse_mailing_domain())
        # switching back from partner mode restores standard compute
        mailing.recipient_selection = 'partner'
        mailing.partner_ids = [(6, 0, self.partner_a.ids)]
        mailing.recipient_selection = 'domain'
        self.assertEqual(
            mailing.mailing_domain,
            repr(mailing._get_default_mailing_domain()))
        mailing.action_put_in_queue()
        self.assertEqual(mailing.state, 'in_queue')
{
    'name': 'HR Leave Mandatory Support Document (PSC)',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Wajib dokumen pendukung untuk tipe cuti tertentu',
    'description': """
HR Leave Mandatory Support Document
===================================
Menambahkan opsi "Wajib Dokumen Pendukung" pada Tipe Cuti.
Jika aktif, pengajuan cuti dengan tipe tersebut tidak dapat
disetujui/divalidasi sebelum ada dokumen pendukung yang dilampirkan
melalui mekanisme attachment standar Odoo 18 Community.
""",
    'author': 'putrasabraham-arch',
    'website': 'https://github.com/putrasabraham-arch',
    'license': 'LGPL-3',
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_leave_type_views.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
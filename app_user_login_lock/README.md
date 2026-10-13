# App - User Login Lock (Odoo 18 Community)

## Tujuan

Admin dapat mengunci akses login kasir secara manual tanpa mengarsipkan `res.users`,
mengubah password, atau menghapus transaksi.

## Instalasi

1. Ekstrak folder `app_user_login_lock` ke direktori `custom_addons`.
2. Tambahkan `custom_addons` pada `addons_path` bila belum ada.
3. Restart layanan Odoo 18.
4. Odoo > Apps > Update Apps List.
5. Cari **App - User Login Lock** lalu **Activate**.

Untuk CLI: `./odoo-bin -d NAMA_DATABASE -u app_user_login_lock --stop-after-init`
(dijalankan setelah modul terpasang dan bila perlu meng-upgrade).

## Penggunaan

### Melalui menu aplikasi sendiri (rekomendasi)

- Aplikasi **User Login Lock** muncul di homepage Odoo.
- Buka **User Login Lock > Login Lock Management**.
- Daftar menampilkan satu baris per user yang **dapat dikelola** (nama, login, status lock).
  User ber-grup **Login Lock Manager** dan superuser **tidak pernah muncul** di daftar.
- Klik **Lock Login** untuk menolak login; klik **Unlock Login** untuk mengizinkan lagi.
- Klik **Deactivate** untuk menonaktifkan akun user (setara archive, tanpa perlu hak Settings);
  klik **Activate** untuk mengaktifkan kembali.
- Semua aksi (Lock/Unlock/Deactivate/Activate) tersedia massal via menu **Action** setelah mencentang beberapa baris.
- Jika ada user baru yang belum tampil, klik **Sync Users** pada header daftar.

### Melalui halaman User (opsional / sebelumnya)

- Settings > Users & Companies > Users > pilih akun Kasir.
- Klik **Lock Login** untuk menolak login. Klik **Unlock Login** untuk mengizinkan lagi.
- Cek tab **Account Security** untuk melihat status, admin pengunci, dan waktu penguncian.
- Kolom **Login Locked** serta filter **Login Locked** tersedia pada daftar Users.

## Mekanisme keamanan

- Status `active` tetap `True` saat hanya Lock Login (tidak di-archive).
- Deactivate mengubah `active` menjadi `False` (akun nonaktif tidak bisa login di Odoo).
- `_check_credentials` menolak autentikasi user yang terkunci, termasuk login password dan
  jalur autentikasi lain yang memanggil fungsi bawaan ini.
- `_get_session_token_fields` menambahkan status lock dan nilai random versi sesi.
  Menurut alur session Odoo 18, perubahan ini membuat cookie sesi yang lama gagal diverifikasi
  pada *request berikutnya*. Tidak menghapus tampilan yang sudah terbuka secara instan.
- `_auth_method_bearer` menolak API key di endpoint dengan `auth='bearer'`.
- Saat dibuka kembali, user perlu login ulang menggunakan kredensialnya.
- Tidak mengatur jam kerja otomatis dan tidak membatasi alamat IP; keduanya fitur lanjutan.
- Odoo administrator Settings dan superuser tidak boleh dikelola untuk menghindari lockout.
- Tindakan Lock/Unlock/Deactivate/Activate memerlukan grup **Login Lock Manager**
  di sisi server.

## Hak Akses (grup khusus)

Modul menyediakan grup khusus **Login Lock Manager**
(`app_user_login_lock.group_app_user_login_lock_manager`):

- Pemegang grup dapat membuka aplikasi **User Login Lock**, melihat daftar user,
  dan melakukan Lock/Unlock serta Deactivate/Activate (termasuk massal via menu Action),
  **tanpa memerlukan hak Settings**.
- Akun yang memegang grup ini **tidak dapat dikelola** oleh siapa pun (tidak bisa di-lock
  maupun di-deactivate; dicek di sisi server), juga tidak bisa mengelola dirinya sendiri
  dan tidak bisa mengelola superuser.
- User ber-grup **Login Lock Manager** dan superuser otomatis **dikecualikan** dari daftar
  (filter domain + constraint server + `Sync Users` membersihkan data lama).
- Pengguna ber-grup **Settings** otomatis menjadi **Login Lock Manager**
  (grup di-*implied* dari `base.group_system`), jadi admin lama tetap punya akses.
- Untuk memberi hak ke staf lain: Settings > Users > pilih user > Access Rights >
  centang **Login Lock Manager** pada kategori **App - User Login Lock**.

## Checklist UAT sebelum produksi

1. User kasir aktif dapat login sebelum dikunci.
2. Admin Lock Login kasir; kasir gagal login dari browser baru.
3. Tab/browser kasir yang sudah login gagal menjalankan operasi setelah lock dan
   akan diminta login ulang saat request berikutnya.
4. Admin Unlock Login; kasir dapat login baru; sesi yang lama tidak kembali valid.
5. Pengguna lain tetap dapat login.
6. Kasir tidak bisa memanggil action Lock/Unlock lewat RPC.
7. Admin tidak bisa lock diri sendiri, superuser, atau user Settings lain.
8. Jika memakai multi-worker/reverse proxy/OAuth/POS, ulangi pengujian di staging
   pada jalur dan deployment tersebut.

> Batas: request yang sudah dieksekusi sebelum transaksi penguncian selesai
> tidak bisa dibatalkan. Perubahan ini bukan kontrol IP/jam kerja.

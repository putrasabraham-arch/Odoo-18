# Product Favorite Access

Modul ini menyediakan akses khusus untuk fitur Star/Favorite pada Produk di Odoo 18.

## Fitur

- ✅ Membuat grup akses baru: **"Akses Star Product"**
- ✅ Mendefinisikan akses untuk membaca dan menulis status favorite/star pada produk
- ✅ Memungkinkan user mengakses dan mengklik bintang pada halaman produk
- ✅ Implementasi field-level security untuk kontrol granular

## Struktur Module

```
product_favorite_access/
├── __manifest__.py                    # Manifest file module
├── __init__.py                        # Init file
├── models/
│   └── __init__.py                    # Models init
├── security/
│   ├── product_favorite_groups.xml    # Definisi grup "Akses Star Product"
│   ├── ir.model.access.csv            # Access rights untuk model
│   └── product_favorite_security.xml  # Field security rules
└── README.md                          # File ini

```

## Instalasi

1. Pastikan module berada di folder `custom_addons` di Odoo instance
2. Update app list dari menu Settings > Apps > Update App List
3. Cari "Product Favorite Access" dan klik Install
4. Setelah terinstall, akses baru akan tersedia di Settings > Users & Companies > Groups

## Penggunaan

### Memberikan Akses kepada User

1. Buka **Settings** > **Users & Companies** > **Users**
2. Pilih user yang ingin diberi akses star product
3. Scroll ke bagian "Access Rights"
4. Centang **"Akses Star Product"** pada kategori Product
5. Klik Save

### Fitur yang Diaktifkan

Setelah user diberi grup "Akses Star Product", mereka dapat:

- ✅ Membaca/melihat status star pada produk
- ✅ Mengklik bintang untuk menandai produk sebagai favorit
- ✅ Memodifikasi status favorite dari view list maupun detail
- ✅ Melihat produk yang mereka tandai sebagai favorite

## Access Rights yang Didefinisikan

### CSV Access Rights (ir.model.access.csv)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_product_template_star,product.template star access,model_product_template,product_favorite_access.group_product_star_access,1,1,0,0
```

**Penjelasan Permission:**
- `perm_read`: 1 (User dapat membaca produk dan status star)
- `perm_write`: 1 (User dapat memodifikasi status favorite)
- `perm_create`: 0 (User tidak dapat membuat produk baru)
- `perm_unlink`: 0 (User tidak dapat menghapus produk)

### Record Rule (product_favorite_security.xml)

Mendefinisikan rule yang memastikan:
- User dapat membaca semua produk (`perm_read = True`)
- User dapat menulis status favorite (`perm_write = True`)
- Domain: Semua produk dapat diakses (`domain_force = [(1, '=', 1)]`)

## Konfigurasi Lebih Lanjut

Jika Anda ingin mengubah permission atau menambahkan batasan khusus:

### 1. Mengubah Permission

Edit file `security/ir.model.access.csv`:

```csv
# Contoh: Hanya read-only (tidak bisa edit star)
access_product_template_star,product.template star access,model_product_template,product_favorite_access.group_product_star_access,1,0,0,0
```

### 2. Menambahkan Domain Restriction

Edit file `security/product_favorite_security.xml` untuk membatasi akses berdasarkan kondisi tertentu:

```xml
<!-- Hanya produk dari kategori tertentu -->
<field name="domain_force">[('categ_id', '=', ref('product.categ_all'))]</field>
```

## Troubleshooting

### User tidak bisa melihat tombol Star

1. Pastikan user sudah ditambahkan ke grup "Akses Star Product"
2. Refresh page atau logout-login kembali
3. Cek logs untuk error message

### Error permission denied

Jika melihat error permission denied:
1. Pastikan group `group_product_star_access` sudah tercreate
2. Jalankan kembali "Update App List" dan reinstall module
3. Clear browser cache

## Support

Jika ada pertanyaan atau issue, silakan hubungi tim development.

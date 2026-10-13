# CJ Member Loyalty Extension (Real)

Odoo 18 module yang **extend** (bukan mengganti) modul `loyalty` standar.

## Fitur

1. **Loyalty Point Calculation** — tetap menggunakan loyalty Odoo standard.
   - Opt-in: `loyalty.rule.points_per_unit` (default `0`). Jika diisi
     `100000`, perhitungan menjadi `floor(total / 100000)`.
   - Program tanpa field ini menggunakan formula bawaan Odoo
     (`reward_point_amount * amount_paid`).
2. **Point History** — model baru `loyalty.point.history` dengan field
   `partner_id`, `order_id`, `invoice_id`, `transaction_date`, `points`,
   `expiry_date`, `status`.
3. **Auto-sync** — setiap `loyalty.history` baru (issued > 0) otomatis
   membuat baris `loyalty.point.history`.
4. **Expiry 365 hari** — `expiry_date = transaction_date + 365 hari`.
5. **Cron harian** — `ir_cron_cja_expire_points` menandai batch lewat
   expire dan mengurangi saldo loyalty card.
6. **Customer bon (21 hari)** — saat invoice `out_invoice` lunas, jika
   `payment_date - invoice_date > 21` hari, poin otomatis di-cancel
   dan saldo loyalty card dikurangi.
7. **Print report tanpa nominal** — opt-in:
   `loyalty.program.hide_points_nominal_on_print` (default `False`).
   Jika dicentang, gift card print report tidak menampilkan nominal
   nilai poin.

## Struktur

```
cj_member_loyalty_extension_real/
├── __manifest__.py
├── __init__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── account_move.py         # 21-day payment rule
│   ├── loyalty_history.py      # sync ke loyalty.point.history
│   ├── loyalty_point_history.py # NEW
│   ├── loyalty_program.py      # hide_points_nominal_on_print
│   ├── loyalty_rule.py         # points_per_unit
│   └── sale_order.py           # opt-in floor rule
├── views/
│   ├── loyalty_history_views.xml
│   ├── loyalty_point_history_menus.xml
│   ├── loyalty_point_history_views.xml
│   ├── loyalty_program_views.xml
│   ├── loyalty_report_templates.xml
│   └── loyalty_rule_views.xml
├── security/
│   └── ir.model.access.csv
└── data/
    └── cron_data.xml
```

## Cara Install

### 1. Copy module

```bash
cp -r cj_member_loyalty_extension_real \
  /path/to/odoo18/custom_addons/
```

### 2. Update `--addons-path`

Pastikan `custom_addons` masuk di `odoo.conf`:

```ini
addons_path = /path/to/odoo18/addons,/path/to/odoo18/custom_addons
```

### 3. Restart & update

```bash
./odoo-bin -c odoo.conf -u cj_member_loyalty_extension_real
```

Atau dari UI: **Apps → Update Apps List → Install**.

### 4. Konfigurasi Loyalty Rule (opsional, untuk floor rule)

* Buka **Sales ‣ Products ‣ Discount & Loyalty**.
* Pilih / buat program loyalty, buka tab **Rules**.
* Set **Reward point mode = Money**, lalu isi **Currency per 1 Point**
  dengan `100000` untuk aktivasi floor rule.

Jika field ini kosong (`0`), program berjalan dengan formula standar
Odoo (`reward_point_amount * amount_paid`).

### 5. Konfigurasi Print Report (opsional)

* Buka program loyalty.
* Centang **Hide Points Nominal on Print** untuk menyembunyikan nilai
  nominal pada gift card print report.

### 6. Cron

Cron `CJA Loyalty: Expire Points Daily` otomatis terpasang. Bisa dicek
di **Settings ‣ Technical ‣ Scheduled Actions**.

### 7. Menu Akses

Menu **Loyalty Point History** muncul di:

**Sales ‣ Products ‣ Discount & Loyalty ‣ Loyalty Point History**

## Security

| Group | Akses |
|---|---|
| Salesman (`sales_team.group_sale_salesman`) | Read loyalty point history, read loyalty rule |
| Sales Manager (`sales_team.group_sale_manager`) | Full access loyalty point history, manage loyalty program |

## Catatan Penting

* **Core Odoo tidak diubah** — semua perubahan menggunakan `_inherit`.
* **Formula floor adalah opt-in** — jika `points_per_unit = 0`, Odoo
  berjalan seperti biasa.
* **Hide nominal adalah opt-in** — jika `hide_points_nominal_on_print = False`,
  print report seperti bawaan Odoo.
* **21-day rule otomatis aktif** — saat invoice paid, system cek window.
* **Tidak membuat loyalty baru** — module ini extend loyalty bawaan.
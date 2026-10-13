{
    'name': 'Product Favorite Access',
    'version': '18.0.1.0.0',
    'category': 'Product',
    'author': 'Custom Development',
    'summary': 'Custom access rights untuk fitur Star/Favorite pada Produk',
    'description': """
        Modul ini menyediakan akses khusus untuk fitur Star/Favorite pada Product.
        Menambahkan grup "Akses Star Product" yang memungkinkan user untuk:
        - Membaca dan memodifikasi status favorite/star pada produk
        - Mengakses dan mengklik bintang pada halaman produk
    """,
    'depends': ['product', 'base'],
    'data': [
        'security/product_favorite_groups.xml',
        'security/product_favorite_access_rights.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

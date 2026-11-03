# Master Data CRUD

Aplikasi CRUD Master Data berbasis Django, PostgreSQL, Docker, dan Bootstrap 5 dengan antarmuka Start Bootstrap SB Admin 7.0.7.

## Fitur
- CRUD Dapur, Jadwal, Toko, dan Template Produk.
- Login multi-user dan role Admin Master / Editor Master / Viewer Master.
- Impor dan ekspor Excel (.xlsx).
- Pencarian data, dashboard ringkas, dan Django Admin.
- PostgreSQL 16 melalui Docker Compose.

## Menjalankan
```bash
cp .env.example .env
# Ubah SECRET_KEY dan POSTGRES_PASSWORD pada .env
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_master
```
Buka http://localhost:7070. Admin Django tersedia di /django-admin/.

## Hak akses
Tambahkan pengguna melalui Django Admin dan masukkan ke salah satu grup:
- Admin Master: lihat, tambah, ubah, hapus.
- Editor Master: lihat, tambah, ubah.
- Viewer Master: hanya lihat dan ekspor.

Superuser memiliki akses penuh.

## Format Excel
Kolom Dapur: `kode_dapur,nama_dapur,operation_type,document`.
Jadwal: `kode_jadwal,jadwal_kirim`.
Toko: `kode_toko,nama_toko`.
Template Produk: `kode_produk,nama_produk,kode_dapur`.

Baris pertama harus berupa header. Untuk template produk, kode_dapur harus sudah ada di master Dapur.


## Frontend
- Admin dashboard menggunakan [Start Bootstrap SB Admin 7.0.7](https://github.com/StartBootstrap/startbootstrap-sb-admin).
- Layout Django berada di `templates/base.html`; halaman dashboard dan master data berada di `templates/masterdata/`.
- Asset SB Admin 7.0.7 dimuat melalui CDN; penyesuaian RO berada di `static/css/sb-admin-overrides.css`.
- Tema Light, Dark, Ocean, Forest, dan Sunset tetap tersedia.
- SB Admin dirilis dengan lisensi MIT. Salinan pemberitahuan lisensi disertakan pada `licenses/SB-ADMIN-MIT-LICENSE.txt`.

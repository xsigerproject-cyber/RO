# Detailed Design Specification (DDS)
## Aplikasi Master Data (RO)

| Atribut | Nilai |
|---|---|
| Produk | Aplikasi Master Data |
| Repository | `xsigerproject-cyber/RO` |
| Branch acuan | `main` |
| Status dokumen | Desain teknis berdasarkan implementasi repository |
| Tanggal | 3 November 2026 |

## Dokumen Terkait

Alasan bisnis dan rekonstruksi keputusan percakapan dicatat pada [`doc/DECISION_LOG.md`](DECISION_LOG.md). Dokumen ini menjelaskan desain teknis; keputusan kebutuhan tetap merujuk pada PRD.

## 1. Tujuan Dokumen

DDS menjelaskan struktur teknis, komponen, model data, alur proses, endpoint, keamanan, dan deployment aplikasi berdasarkan source code repository. Detail yang belum diimplementasikan ditandai sebagai catatan, bukan diasumsikan tersedia.

## 2. Arsitektur Sistem

### 2.1 Komponen

| Komponen | Teknologi | Tanggung jawab |
|---|---|---|
| Browser | HTML, CSS, JavaScript, Bootstrap 5 | Antarmuka pengguna |
| Web application | Django 5.1+ | Routing, autentikasi, validasi, CRUD, impor/ekspor |
| WSGI server | Gunicorn | Menjalankan Django WSGI |
| Static middleware | WhiteNoise | Penyajian static files |
| Database | PostgreSQL 16 | Persistensi data |
| Container runtime | Docker Compose | Menjalankan service web dan database |
| Excel processing | openpyxl | Membaca dan membuat file XLSX |

### 2.2 Topologi Deployment

```text
Browser
   |
   | HTTP :7070
   v
Docker host
   |
   v
web container (Django + Gunicorn :8000)
   |             |
   |             +-- WhiteNoise / static files
   |
   | PostgreSQL connection (service db :5432)
   v
db container (PostgreSQL 16)
   |
   v
Docker volume: postgres_data
```

Docker Compose memetakan port host `7070` ke port container web `8000`. Database menggunakan named volume `postgres_data`.

### 2.3 Startup Container

Entrypoint web menjalankan urutan:
1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput`
3. `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3`

Service database memiliki healthcheck `pg_isready`; service web menunggu database sehat.

## 3. Struktur Source Code

| Path | Fungsi |
|---|---|
| `config/settings.py` | Konfigurasi Django, database, middleware, template, static files, timezone |
| `config/urls.py` | URL admin Django, login/logout, include URL masterdata |
| `masterdata/models.py` | Model Dapur, Jadwal, Toko, TemplateProduk, UserProfile |
| `masterdata/forms.py` | ModelForm dan Bootstrap widget styling |
| `masterdata/views.py` | Dashboard, daftar, CRUD, pencarian, Excel, theme |
| `masterdata/urls.py` | Routing fitur masterdata |
| `masterdata/permissions.py` | Fungsi pemeriksaan hak akses |
| `masterdata/context_processors.py` | Menyediakan tema aktif ke template |
| `masterdata/migrations/` | Skema database dan seed data |
| `templates/` | Template HTML Django |
| `static/` | CSS dan JavaScript aplikasi |
| `Dockerfile` | Image aplikasi |
| `docker-compose.yml` | Definisi service web dan db |
| `entrypoint.sh` | Startup migration, collectstatic, Gunicorn |

## 4. Desain Data

### 4.1 Entity Relationship

```mermaid
erDiagram
    DAPUR ||--o{ TEMPLATE_PRODUK : "memiliki"
    USER ||--o| USER_PROFILE : "memiliki"

    DAPUR {
        int kode_dapur PK
        string nama_dapur
        string operation_type
        string document
    }
    JADWAL {
        int kode_jadwal PK
        string jadwal_kirim
    }
    TOKO {
        int kode_toko PK
        string nama_toko
    }
    TEMPLATE_PRODUK {
        int kode_produk PK
        string nama_produk
        int dapur_id FK
    }
    USER_PROFILE {
        bigint id PK
        int user_id FK
        string theme
    }
    USER {
        int id PK
        string username
    }
```

### 4.2 Definisi Tabel

#### Dapur
| Kolom | Tipe Django | Constraint |
|---|---|---|
| kode_dapur | PositiveIntegerField | Primary key |
| nama_dapur | CharField(120) | Wajib |
| operation_type | CharField(120) | Wajib |
| document | CharField(60) | Wajib |

#### Jadwal
| Kolom | Tipe Django | Constraint |
|---|---|---|
| kode_jadwal | PositiveIntegerField | Primary key |
| jadwal_kirim | CharField(120) | Wajib |

#### Toko
| Kolom | Tipe Django | Constraint |
|---|---|---|
| kode_toko | PositiveIntegerField | Primary key |
| nama_toko | CharField(120) | Wajib |

#### TemplateProduk
| Kolom | Tipe Django | Constraint |
|---|---|---|
| kode_produk | PositiveIntegerField | Primary key |
| nama_produk | CharField(160) | Wajib |
| dapur_id | ForeignKey ke Dapur | NOT NULL, ON DELETE PROTECT |

Relasi produk ke dapur menggunakan `related_name="produk"`. Primary key Dapur disimpan pada kolom relasi `dapur_id`; dalam file Excel kolom tersebut dipertukarkan menggunakan header `kode_dapur`.

#### UserProfile
| Kolom | Tipe Django | Constraint |
|---|---|---|
| id | BigAutoField | Primary key |
| user_id | OneToOneField ke User | Unique, ON DELETE CASCADE |
| theme | CharField(10) | Default `light`; choices light/dark/ocean/forest/sunset |

Signal `post_save` pada User membuat UserProfile saat user baru dibuat dan memastikan profile tersedia saat user disimpan kembali.

### 4.3 Urutan Data Master

- TemplateProduk bergantung pada Dapur.
- Dapur, Jadwal, dan Toko berdiri sendiri.
- Penghapusan Dapur yang masih direferensikan oleh TemplateProduk ditolak oleh constraint `PROTECT`.

## 5. Desain Data Awal (Seed)

Migration `0003_seed_master_data.py` bergantung pada migration `0002_userprofile` dan menggunakan historical models melalui `apps.get_model`.

Urutan proses:
1. Upsert enam record Dapur.
2. Upsert tiga record Jadwal.
3. Upsert enam record Toko.
4. Ambil Dapur berdasarkan kode 15 dan 14, lalu upsert enam record Template Produk dengan foreign key yang sesuai.

Operasi menggunakan database alias dari `schema_editor.connection.alias` dan `update_or_create` berdasarkan primary key.

Jumlah target setelah migration pada database baru:
- Dapur: 6
- Jadwal: 3
- Toko: 6
- Template Produk: 6

Reverse operation migration adalah `RunPython.noop`; rollback migration tidak menghapus data seed secara otomatis.

## 6. Routing dan Endpoint

Semua endpoint di bawah ini berada di root URL aplikasi kecuali prefix yang ditampilkan.

| Method | URL | Django route name | Fungsi |
|---|---|---|---|
| GET | `/` | dashboard | Dashboard |
| GET | `/dapur/`, `/jadwal/`, `/toko/`, `/produk/` | master_list | Daftar dan pencarian |
| GET/POST | `/<kind>/add/` | master_create | Form tambah |
| GET/POST | `/<kind>/<pk>/edit/` | master_edit | Form ubah |
| POST | `/<kind>/<pk>/delete/` | master_delete | Hapus |
| GET | `/<kind>/export/` | export_excel | Ekspor XLSX |
| GET | `/<kind>/import-template/` | download_import_template | Unduh template XLSX |
| POST | `/<kind>/import/` | import_excel | Impor XLSX |
| POST | `/theme/set/` | set_theme | Simpan tema |
| GET | `/accounts/login/` | login | Login Django |
| POST | `/accounts/logout/` | logout | Logout Django |
| Django admin | `/django-admin/` | admin | Administrasi Django |

Parameter `kind` yang didukung: `dapur`, `jadwal`, `toko`, dan `produk`. Nilai lain menghasilkan HTTP 404 melalui fungsi konfigurasi master.

## 7. Desain Proses Aplikasi

### 7.1 Autentikasi dan Otorisasi

- View utama menggunakan decorator `login_required`.
- Login menggunakan Django LoginView dengan template `registration/login.html`.
- Logout menggunakan Django LogoutView melalui POST form pada navbar.
- `can_manage(user)`: true untuk superuser atau anggota grup Admin Master/Editor Master.
- `can_delete(user)`: true untuk superuser atau anggota grup Admin Master.
- Pembuatan dan pengelolaan grup dilakukan melalui Django Admin sesuai konfigurasi yang tersedia.

### 7.2 Daftar dan Pencarian

1. View menerima `kind` dan memuat konfigurasi model, form, daftar field, dan judul.
2. Queryset awal mengambil seluruh objek model.
3. Jika parameter `q` terisi, view membangun kondisi pencarian.
4. Field teks memakai pencarian `icontains`.
5. Field integer dicari sebagai nilai eksak jika query berupa digit.
6. Pada produk, pencarian juga memeriksa `dapur__nama_dapur` dan `dapur__kode_dapur`.
7. Template daftar dirender dengan queryset, form tambah bila user berhak, dan flag izin.

### 7.3 Tambah dan Ubah

1. View memeriksa `can_manage`; jika tidak berhak, mengembalikan HTTP 403.
2. Untuk edit, objek diambil berdasarkan primary key.
3. Form ModelForm dibuat dari POST dan instance terkait.
4. Jika valid, form disimpan dan pengguna diarahkan ke daftar master.
5. Jika tidak valid, halaman form atau daftar dengan modal tambah ditampilkan kembali bersama error validasi.

### 7.4 Hapus

1. View memeriksa `can_delete`.
2. Hanya method POST diterima.
3. Objek dicari berdasarkan primary key.
4. Objek dihapus dan pengguna diarahkan kembali ke daftar.
5. Constraint relasi Dapur-Produk melindungi Dapur yang masih dipakai.

### 7.5 Impor XLSX

1. Periksa hak kelola.
2. Pastikan file tersedia, ukuran tidak lebih dari 5 MB, dan ekstensi `.xlsx`.
3. Buka workbook dengan openpyxl dalam mode read-only dan data-only.
4. Baca header dan pastikan semua kolom wajib tersedia.
5. Iterasi baris mulai baris kedua; lewati baris kosong.
6. Parse primary key menjadi integer.
7. Untuk produk, ubah input `kode_dapur` menjadi nilai foreign key `dapur`.
8. Trim nilai teks.
9. Cari instance berdasarkan primary key.
10. Validasi dengan ModelForm; simpan jika valid.
11. Semua baris diproses di dalam `transaction.atomic()`; error akan membatalkan transaksi.
12. Tampilkan pesan sukses atau error kepada pengguna.

Catatan: kode importer memetakan header ke dictionary berdasarkan nama kolom; header duplikat tidak secara eksplisit ditolak pada implementasi saat ini.

### 7.6 Template XLSX

1. Periksa hak kelola.
2. Buat workbook dan tulis header sesuai konfigurasi model.
3. Ambil record pertama dengan `order_by(model._meta.pk.name).first()`.
4. Jika record tersedia, tulis nilai field ke baris kedua.
5. Untuk relasi produk, tulis `sample_obj.dapur_id` pada kolom `kode_dapur`.
6. Jika tidak ada record, jangan tulis baris contoh.
7. Format header dan baris contoh; beri komentar pada sel contoh.
8. Bekukan baris header dan aktifkan autofilter.
9. Kembalikan file sebagai attachment XLSX.

Baris contoh adalah record yang benar-benar ada di database. Jika baris tersebut diimpor tanpa perubahan, importer akan menemukan primary key yang sama dan memperbarui record tersebut.

### 7.7 Ekspor XLSX

1. Ambil seluruh record pada model yang dipilih.
2. Tulis header dari konfigurasi field.
3. Iterasi objek dan tulis nilai setiap field.
4. Untuk field relasi produk, tulis `dapur_id` pada kolom `kode_dapur`.
5. Kembalikan workbook sebagai file XLSX.

### 7.8 Pengaturan Tema

1. Terima POST pada `/theme/set/`.
2. Baca nilai `theme`.
3. Validasi terhadap pilihan tema UserProfile.
4. Ambil atau buat profile pengguna.
5. Simpan tema dan kembalikan JSON status.

## 8. Validasi dan Penanganan Kesalahan

- Form CRUD menggunakan Django ModelForm.
- Field primary key impor harus integer positif sesuai model.
- Upload dibatasi 5 MB dan hanya ekstensi `.xlsx`.
- Header yang hilang menghasilkan pesan validasi.
- Foreign key produk harus menunjuk Dapur yang valid.
- Error validasi impor ditampilkan melalui Django messages.
- Error tak terduga dicatat melalui Python logger dan pesan umum ditampilkan.
- Akses tanpa hak menghasilkan HTTP 403; kind tidak dikenal menghasilkan HTTP 404; method yang tidak diizinkan pada delete menghasilkan HTTP 405.

## 9. Konfigurasi dan Environment

Environment variables yang dibaca:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Default database host pada settings adalah `localhost`, sedangkan deployment Compose harus menggunakan hostname service database `db` pada konfigurasi environment.

Pengaturan aplikasi:
- Bahasa: `id-id`
- Timezone: `Asia/Jakarta`
- Static URL: `/static/`
- Static root: `staticfiles/`
- Static source: `static/`

## 10. Keamanan

- Gunakan nilai `SECRET_KEY` yang kuat dan rahasia pada deployment.
- Jangan aktifkan `DEBUG` pada production.
- Atur `ALLOWED_HOSTS` sesuai hostname/IP server.
- Gunakan password PostgreSQL yang kuat dan jangan commit file `.env`.
- Operasi perubahan data dilindungi pemeriksaan hak akses server-side.
- Form POST Django menggunakan CSRF middleware; template form perlu menyertakan token CSRF.
- Gunakan HTTPS melalui reverse proxy jika aplikasi diakses melalui jaringan yang tidak tepercaya.

Catatan: konfigurasi HTTPS/reverse proxy, rate limiting, audit log, dan kebijakan backup tidak didefinisikan oleh file deployment yang ditinjau.

## 11. Operasional dan Deployment

Contoh alur instalasi/update pada server:

```bash
cp .env.example .env
# Isi SECRET_KEY, kredensial PostgreSQL, ALLOWED_HOSTS, dan POSTGRES_HOST=db
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

Untuk update repository yang sudah terpasang:

```bash
git pull origin main
docker compose up -d --build
```

Entrypoint otomatis menjalankan migration dan collectstatic saat container web dimulai. Named volume database bernama `postgres_data`; perintah yang menghapus volume dapat menghilangkan data persisten dan tidak boleh digunakan sebagai langkah update rutin.

## 12. Verifikasi Teknis yang Disarankan

Sebelum rilis, jalankan dan verifikasi pada lingkungan target:
1. `python manage.py check`
2. `python manage.py showmigrations`
3. `python manage.py migrate --check` (jika tersedia pada versi Django yang digunakan)
4. Uji login, logout, dan setiap role.
5. Uji CRUD keempat master.
6. Uji proteksi penghapusan Dapur yang masih memiliki Produk.
7. Uji impor file valid, header salah, ukuran melebihi batas, ekstensi salah, primary key tidak valid, dan foreign key Dapur tidak ditemukan.
8. Uji rollback transaksi ketika salah satu baris impor tidak valid.
9. Uji ekspor dan template pada tabel berisi data maupun kosong.
10. Pastikan file CSS/JS static dapat diakses dari browser.

Dokumen ini adalah spesifikasi berdasarkan source code yang ditinjau; daftar verifikasi di atas bukan klaim bahwa seluruh pengujian telah dijalankan.


## 13. Status Template Produk dan Sinkronisasi Draft RO

### 13.1 Perubahan Model Data

Model `TemplateProduk` menambahkan field:
| Kolom | Tipe Django | Default | Keterangan |
|---|---|---|---|
| is_active | BooleanField | True | Menentukan apakah produk dapat digunakan pada RO baru dan Draft berjalan |

Migration `0005_templateproduk_is_active.py` menambahkan kolom tersebut. Record lama memperoleh nilai default `True`, sehingga produk yang sudah ada tetap tersedia setelah migration.

### 13.2 Form dan Daftar Master

- ModelForm Template Produk menampilkan field `is_active` sebagai checkbox Aktif.
- Daftar Template Produk menampilkan label Aktif atau Nonaktif.
- Field status turut disertakan dalam konfigurasi impor/ekspor Excel Template Produk.

### 13.3 Sinkronisasi Draft

Fungsi `_sync_draft_products` di `masterdata/ro_views.py` menerima kunci transaksi (Tanggal RO, Toko, Dapur, Jadwal) dan melakukan:
1. Mengambil produk Template Produk berstatus Aktif untuk Dapur tersebut.
2. Menghapus baris produk Nonaktif dari RO berstatus Draft pada kunci transaksi yang sama.
3. Mempertahankan baris produk yang masih Aktif, termasuk nilai Qty-nya.
4. Membuat baris RO baru dengan Qty 0 untuk produk Aktif yang belum ada pada Draft.
5. Tidak mengubah baris RO berstatus Terkirim.

Sinkronisasi dijalankan saat halaman transaksi Draft dibuka dan sebelum Draft disimpan/dikirim. Daftar produk diurutkan berdasarkan kode produk saat ditampilkan.

### 13.4 Batasan dan Verifikasi

- Produk Nonaktif yang sudah berada di RO Terkirim tetap tersimpan sebagai bagian dari riwayat transaksi.
- Mengaktifkan kembali produk menggunakan record Template Produk yang sama.
- Verifikasi yang perlu dilakukan pada lingkungan target: migration, form tambah/edit Template Produk, impor/ekspor status, sinkronisasi produk aktif/nonaktif pada Draft, dan kekekalan RO Terkirim.
- Pembaruan repository ini belum merupakan bukti bahwa migration atau pengujian telah dijalankan pada server produksi.


## 14. Desain Fitur Administrasi Data dan Inisialisasi (Rencana)

<badge>Desain; belum diimplementasikan</badge>

Bagian ini adalah rancangan fitur pembersihan data testing sebelum Go-Live, bukan deskripsi endpoint atau kode yang sudah tersedia.

### 14.1 Otorisasi

- Buat pemeriksaan izin khusus Administrator sesuai definisi peran RO pada PRD.
- Pemeriksaan dilakukan pada setiap view/action di server-side. Jangan menggunakan `can_delete` atau `can_manage` sebagai pengganti izin Administrator.
- Superuser boleh dianggap memiliki izin Administrator.
- Semua operasi mutasi menggunakan POST dan CSRF protection.
- Akses tanpa izin menghasilkan HTTP 403.

### 14.2 Penghapusan Template Produk

Sediakan tiga cakupan: satu produk, seluruh produk pada satu Dapur, dan seluruh Template Produk.

Untuk setiap cakupan:
1. Ambil target berdasarkan kode produk/Dapur atau seluruh queryset.
2. Hitung jumlah target dan jumlah target yang masih direferensikan oleh RO.
3. Tampilkan halaman konfirmasi berisi cakupan, jumlah target, dan informasi blokir referensi.
4. Jika ada referensi RO, tolak penghapusan tanpa mengubah data.
5. Jika tidak ada referensi, hapus target dalam `transaction.atomic()`.
6. Catat tindakan pada audit log yang dipertahankan.

Jangan memakai cascade yang menghapus RO secara implisit. Relasi `PROTECT` tetap menjadi pengaman integritas data.

### 14.3 Inisialisasi Data Testing

Urutan operasi dalam satu `transaction.atomic()`:
1. Validasi pemanggil adalah Administrator.
2. Validasi metode POST, CSRF, dan nilai konfirmasi persis `RESET DATA`.
3. Hitung jumlah baris RO dan Template Produk untuk ringkasan.
4. Hapus seluruh baris RO, termasuk Draft dan Terkirim.
5. Hapus seluruh Template Produk.
6. Simpan catatan audit berisi pelaku, timestamp, jenis tindakan, dan jumlah record yang dihapus.
7. Commit transaksi.

Jika penghapusan atau pencatatan audit gagal, rollback seluruh transaksi. Implementasi audit harus memastikan catatan inisialisasi tidak ikut terhapus; catatan dapat dibuat setelah penghapusan target dalam transaksi yang sama atau disimpan pada sistem log terpisah.

### 14.4 Data yang Dipertahankan

Inisialisasi hanya mengosongkan data RO dan Template Produk. Jangan menghapus/truncate Dapur, Jadwal, Toko, User, Group/Permission, UserProfile, konfigurasi aplikasi, migration history, maupun log audit yang harus dipertahankan. Jangan menjalankan `flush`, menghapus schema/database, menghapus volume Docker, atau mereset sequence secara otomatis.

### 14.5 Backup dan Pemulihan

- UI memberi peringatan untuk membuat backup PostgreSQL penuh sebelum tindakan.
- Backup harus dapat dipulihkan; membuat file backup saja bukan bukti pemulihan.
- Ekspor XLSX tidak mempertahankan seluruh relasi, akun, permission, dan konfigurasi sehingga bukan pengganti backup PostgreSQL.
- Prosedur restore dilakukan di luar fitur reset sesuai prosedur operasional database.

### 14.6 Rancangan UI

- Tambahkan menu khusus Administrator, misalnya **Administrasi Data**.
- Pisahkan area **Hapus Template Produk** dari **Inisialisasi Data Testing**.
- Setiap tindakan menampilkan jumlah data terdampak dan konfirmasi sebelum eksekusi.
- Inisialisasi menggunakan input konfirmasi teks `RESET DATA`.
- Setelah berhasil, tampilkan ringkasan jumlah RO dan Template Produk yang dihapus serta referensi log audit.

### 14.7 Pengujian Wajib Sebelum Rilis

- Uji akses Administrator, superuser, Admin Master, Editor Master, Viewer, Admin Toko, dan Admin Produksi sesuai role yang berlaku.
- Uji penghapusan produk tanpa RO dan produk yang masih direferensikan RO.
- Uji hapus per Dapur dan hapus seluruh Template Produk, termasuk kondisi referensi RO campuran.
- Uji reset ketika ada Draft saja, Terkirim saja, dan keduanya.
- Pastikan Dapur, Jadwal, Toko, user, grup, permission, UserProfile, migration history, dan audit log tetap ada.
- Simulasikan kegagalan setelah penghapusan RO untuk memastikan rollback mengembalikan RO dan Template Produk.
- Uji konfirmasi kosong/salah, request GET, CSRF gagal, dan akses langsung tanpa izin.
- Verifikasi backup dan prosedur restore secara terpisah.

Belum ada URL, nama view, model audit, atau migration yang ditetapkan. Detail implementasi ditentukan saat pekerjaan kode dimulai dan harus diselaraskan dengan source code/migration aktual.


## 15. Modul Administrasi User, Backup, dan Restore

<badge>Implementasi awal pada branch main; verifikasi runtime belum dilakukan</badge>

### 15.1 Struktur Source

| Path | Tanggung jawab |
|---|---|
| `masterdata/admin_forms.py` | Form CRUD user dan validasi password |
| `masterdata/admin_views.py` | Otorisasi Administrator, CRUD user, backup, restore |
| `masterdata/urls.py` | Endpoint `admin-tools/` |
| `masterdata/context_processors.py` | Flag tampilan menu Administrator |
| `templates/admin_tools/` | Dashboard administrasi, user, backup, restore |
| `templates/base.html` | Menu Administrasi khusus Administrator |

### 15.2 Otorisasi
- Decorator `_admin_only` memeriksa login dan `is_administrator(user)` untuk setiap view.
- `is_administrator` mengizinkan grup Administrator atau superuser.
- Endpoint mutasi menggunakan POST dan CSRF middleware Django.
- Menu sidebar menggunakan context processor `administrator_context`; menu tersembunyi bagi role lain. Ini hanya kontrol UI, sedangkan view tetap memeriksa izin server-side.

### 15.3 User Management
- Menggunakan Django User dan Group; tidak membuat tabel user baru.
- Form mengelola username, first/last name, email, is_active, groups, dan pemetaan `UserProfile.toko`.
- Jika grup Admin Toko dipilih, Toko wajib diisi. Jika bukan Admin Toko, field Toko harus kosong.
- User baru diberi unusable password; Administrator mengatur password lewat endpoint terpisah.
- Password divalidasi dengan `validate_password` dan disimpan melalui `set_password`.
- Akun sendiri tidak dapat dihapus; akun superuser tidak dapat dihapus melalui modul; hanya superuser dapat mengubah/mengganti password superuser.
- Perlindungan Administrator aktif terakhir diterapkan untuk menghindari kehilangan seluruh akses administrasi.

### 15.4 Backup
- Image web memasang paket Alpine `postgresql16-client`.
- `pg_dump --format=custom --file <path>` dijalankan dengan kredensial dan koneksi database dari `settings.DATABASES["default"]`.
- Lokasi default: `/var/backups/ro`, dapat diubah melalui `DB_BACKUP_DIR`.
- Compose memasang named volume `db_backups` ke lokasi tersebut; volume ini terpisah dari `postgres_data`.
- Nama file mengikuti pola `ro_db_YYYYMMDD_HHMMSS_<8-hex>.dump`; hanya file yang cocok pola ini ditampilkan/diunduh.
- Unduhan menggunakan FileResponse dan validasi nama file.

### 15.5 Restore
1. Validasi user Administrator, POST, CSRF, ekstensi `.dump`, ukuran maksimum 1 GiB, dan konfirmasi `RESTORE DATABASE`.
2. Salin upload ke file sementara dengan nama UUID di direktori backup.
3. Jalankan `pg_restore --list` untuk memeriksa format arsip.
4. Buat backup otomatis database aktif.
5. Jalankan `pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error --single-transaction --dbname <database> <archive>`.
6. Hapus file upload sementara pada blok finally.
7. Jika perintah gagal, catat detail pada log server dan tampilkan pesan umum; transaksi restore menggunakan single transaction.

**Catatan:** file backup dan upload restore mengandung seluruh data database termasuk data personal dan kredensial hash. Batasi akses server/volume dan jangan mengirim backup melalui kanal publik. File yang hanya ada pada volume `db_backups` tetap berada di host yang sama; salinan off-site diperlukan untuk mitigasi kehilangan server.

### 15.6 Endpoint
| Method | URL | Name | Fungsi |
|---|---|---|---|
| GET | `/admin-tools/` | admin_home | Dashboard administrasi |
| GET | `/admin-tools/users/` | admin_user_list | Daftar user |
| GET/POST | `/admin-tools/users/add/` | admin_user_create | Tambah user |
| GET/POST | `/admin-tools/users/<id>/edit/` | admin_user_edit | Ubah user |
| GET/POST | `/admin-tools/users/<id>/password/` | admin_user_password | Ganti password |
| POST | `/admin-tools/users/<id>/delete/` | admin_user_delete | Hapus user |
| GET | `/admin-tools/backup/` | admin_backup | Daftar backup |
| POST | `/admin-tools/backup/create/` | admin_backup_create | Buat backup |
| GET | `/admin-tools/backup/download/<filename>/` | admin_backup_download | Unduh backup |
| GET | `/admin-tools/restore/` | admin_restore | Form restore |
| POST | `/admin-tools/restore/execute/` | admin_restore_execute | Jalankan restore |

### 15.7 Verifikasi Sebelum Produksi
- Jalankan `docker compose build web` untuk memastikan paket PostgreSQL client tersedia.
- Jalankan `python manage.py check` dan uji seluruh URL/template.
- Uji akses Administrator, superuser, Admin Toko, Admin Produksi, Admin Master, Editor Master, Viewer, dan anonymous.
- Uji CRUD user, mapping Toko Admin Toko, password tidak valid/valid, perlindungan akun sendiri, superuser, dan Administrator aktif terakhir.
- Buat backup dan pastikan file dapat diunduh serta ukurannya masuk akal.
- Restore backup pada database staging terpisah; verifikasi tabel, relasi, akun, dan data.
- Uji restore dengan file rusak dan pastikan database tidak berubah parsial.
- Jangan melakukan uji restore pertama kali pada database produksi.

Belum ada hasil eksekusi test atau restore runtime yang diklaim oleh dokumen ini.


### 15.8 Perbaikan alur Tambah User
- GET ke `/admin-tools/users/add/` selalu merender form kosong.
- POST dengan data tidak valid merender kembali form beserta pesan validasi.
- POST valid membuat user, mengatur unusable password, menampilkan pesan sukses, lalu redirect ke daftar user.
- Perbaikan ini mengatasi view sebelumnya yang tidak mengembalikan HTTP response pada request GET dan tidak melakukan redirect setelah penyimpanan berhasil.
- Pengujian runtime tetap perlu dilakukan setelah deployment.


### 15.9 Penyelarasan tampilan modul Administrasi
- Field pada form user diberi class Bootstrap 5 sesuai jenis widget: `form-control`, `form-select`, dan `form-check-input`.
- Form Tambah/Ubah User menggunakan grid responsif, kelompok Role ditampilkan sebagai checkbox yang tersusun, dan status Aktif menggunakan switch.
- Form password, dashboard, daftar user, backup, dan restore menggunakan pola card, spacing, dan heading yang konsisten dengan SB Admin/Bootstrap 5.
- Perubahan ini hanya pada presentasi; aturan bisnis dan otorisasi tidak berubah.


## 15.10 Manajemen Role / Group

### Endpoint
- `GET /admin-tools/roles/`: daftar Group, jumlah user, jumlah permission.
- `GET/POST /admin-tools/roles/add/`: membuat Group dan menetapkan permission.
- `GET/POST /admin-tools/roles/<group_id>/edit/`: mengubah Group dan permission.
- `POST /admin-tools/roles/<group_id>/delete/`: menghapus Group jika tidak digunakan user.

### Implementasi
- Form `AdminRoleForm` menggunakan model Django `Group` dan relasi `Permission`.
- Permission diurutkan menurut app label, model, dan codename.
- View memakai decorator `_admin_only`; delete memakai POST dan CSRF.
- Daftar role menggunakan agregasi jumlah user unik.
- Penghapusan ditolak jika jumlah user lebih dari nol.
- Role inti `Administrator`, `Admin Toko`, dan `Admin Produksi` dilindungi dari rename dan delete karena nama tersebut dipakai oleh fungsi pemeriksaan role. Permission-nya tetap dapat diedit.
- Tidak ada perubahan model aplikasi atau migration database.


### 15.11 Filter kata kunci permission pada form Role
- Template `templates/admin_tools/role_form.html` menyediakan input pencarian client-side.
- Filter mencocokkan teks permission, app/model, dan codename secara case-insensitive.
- Opsi yang tidak cocok disembunyikan tanpa mengubah status checked, sehingga permission yang sudah dipilih tidak hilang saat difilter.
- Tidak ada perubahan endpoint, model, atau migration.


### 15.12 Tombol Filter permission
- Filter permission pada `templates/admin_tools/role_form.html` diterapkan saat tombol Filter diklik atau Enter ditekan pada input.
- Tombol Bersihkan mengosongkan kata kunci dan mengembalikan seluruh pilihan.
- Tidak ada penyaringan otomatis pada setiap event input.
- Penyaringan hanya mengubah visibilitas opsi di browser; status checkbox tetap utuh.

### 15.13 Perbaikan `AdminUserForm.save()`
- `super().save(commit=True)` pada `ModelForm` sudah menyimpan relasi many-to-many, termasuk `groups`.
- Jangan memanggil `self.save_m2m()` setelah `super().save(commit=True)`; Django hanya menyediakan helper `save_m2m()` pada instance ketika `save(commit=False)` dipakai.
- Setelah user tersimpan, buat/perbarui `UserProfile.toko` seperti sebelumnya. Tidak ada perubahan model atau migration.
- Verifikasi: tambah user dengan role Admin Toko dan Toko terpilih; pastikan user dan relasi Group serta `UserProfile.toko` tersimpan. Uji juga role non-Admin Toko tanpa pemetaan Toko.


## 16. Standar Visual Frontend dan Dashboard

### 16.1 Arah Visual
Acuan visual ditetapkan dalam root `DESIGN.md`. Dokumen tersebut menjelaskan karakter produk, tipografi, warna, komponen, hierarki, aksesibilitas, dan batasan penyegaran UI.

### 16.2 Sistem Tema
- `static/css/themes.css` menyediakan token semantik untuk Light, Dark, Ocean, Forest, dan Sunset.
- Token mencakup latar, permukaan, teks utama/sekunder, border, aksen, fokus, status, input, navbar, dan sidebar.
- Komponen umum menggunakan token tersebut agar tidak bergantung pada warna tema tertentu.
- `static/css/sb-admin-overrides.css` menangani struktur shell dan kontrol pemilih tema.
- Tema tetap disimpan melalui mekanisme UserProfile dan endpoint `/theme/set/`; perubahan ini tidak mengubah backend atau model.

### 16.3 Dashboard
- View dashboard tetap menyediakan hitungan Dapur, Jadwal, Toko, dan Template Produk.
- Template menampilkan Daftar RO sebagai akses transaksi utama.
- Tombol Buat RO hanya ditampilkan untuk Administrator/superuser melalui flag `is_administrator_user`, karena endpoint transaksi RO tidak mengizinkan Admin Produksi membuat RO.
- Dashboard tidak menampilkan metrik Draft/Terkirim atau agregat produksi karena view saat ini belum menyediakannya.

### 16.4 Batasan Verifikasi
Perubahan CSS dan template telah disimpan pada branch `main`. Belum dilakukan browser rendering, click-through, pengukuran kontras otomatis, atau pengujian visual pada lima tema dan breakpoint. Karena itu, konsistensi aktual seluruh komponen belum boleh dinyatakan lulus.


## Penyelarasan CRUD dan pencarian User (2026-11-04)

- Template daftar/form Master Data dan template Manajemen User/Role menggunakan token tema dari `static/css/themes.css`; hindari warna utility Bootstrap hard-coded jika tersedia token semantik.
- Pola halaman mempertahankan endpoint, form Django, validasi, otorisasi, CSRF, dan proses import/export yang sudah ada.
- Daftar User mendukung query parameter `q` dengan pencocokan case-insensitive pada username, first_name, last_name, dan email. Queryset tetap dibatasi oleh view Administrator.
- Filter permission Role yang berjalan di browser dipertahankan; penyegaran tampilan tidak boleh mengubah checkbox yang dipilih atau perilaku filter.
- Tidak ada perubahan model atau migration yang diperlukan untuk lingkup ini.
- Verifikasi browser, aksesibilitas, lima tema, dan breakpoint tetap menjadi pekerjaan validasi terpisah; jangan menyatakan telah lulus tanpa bukti.
## 14. Penambahan Field Operation Type pada Master Dapur

Model `Dapur` mempertahankan `operation_type` dan menambahkan:
| Kolom | Tipe Django | Constraint |
|---|---|---|
| operation_type_kirim | CharField(120) | Wajib, teks bebas |
| operation_type_terima | CharField(120) | Wajib, teks bebas |

Kedua field baru merupakan teks bebas, mengikuti tipe dan batas panjang field `operation_type`. Migration `0007_dapur_operation_types.py` menambahkan kedua kolom; record Dapur yang sudah ada diisi string kosong saat migration agar data lama tetap terjaga. Setelah migration, form baru meminta nilai field sesuai validasi CharField wajib.

Konfigurasi CRUD Dapur memasukkan kedua field pada daftar dan pencarian. Karena form Dapur menggunakan ModelForm dengan `fields = "__all__"`, kedua field otomatis tersedia pada form tambah dan ubah. Konfigurasi field yang sama juga mengikutsertakannya pada header/baris template impor, validasi impor, dan ekspor Excel. Tidak ada perubahan pada Jadwal, Toko, Template Produk, RO, endpoint, atau otorisasi.


## 17. Adaptasi Antarmuka SAP Fiori-inspired (2026-11-04)

- Referensi HTML demo digunakan untuk pola shell biru gelap, sidebar berkelompok, Inter, ikon Font Awesome, aksen biru, komponen tabel/form, dan dashboard berbasis tile.
- Implementasi berada pada `templates/base.html`, `templates/masterdata/dashboard.html`, `static/css/themes.css`, dan `static/css/sb-admin-overrides.css`.
- Theme switcher dan penyimpanan tema UserProfile tetap memakai endpoint yang sama. Lima tema dipertahankan.
- Dashboard hanya menggunakan `counts.dapur`, `counts.jadwal`, `counts.toko`, `counts.produk`, serta tautan transaksi yang sudah ada. Tidak ada query KPI baru.
- Tidak ada perubahan model, migration, endpoint, validasi, permission, atau aturan RO.
- Google Fonts Inter dan Font Awesome menggunakan CDN; tampilan font/ikon memerlukan koneksi browser ke sumber CDN. Font stack fallback tetap tersedia.
- Verifikasi browser, responsivitas aktual, kontras, click-through, dan lima tema belum dilakukan.

## 18. Pengaturan Koneksi Odoo — Tahap 1

### Data model
Model `OdooConnectionSetting` menyimpan satu konfigurasi (singleton, primary key tetap `id=1`):
- `base_url`: URL dasar instance Odoo.
- `database`: nama database, opsional.
- `username`: label/identitas user integrasi untuk administrasi; autentikasi JSON-2 dilakukan oleh API Key yang terikat pada pemilik key di Odoo.
- `api_key_encrypted`: token Fernet, bukan plaintext.
- `last_tested_at`, `connection_status`, `connection_message`, `updated_at`: status koneksi dan metadata.

Migration: `0008_odooconnectionsetting.py`, bergantung pada `0007_dapur_operation_types`.

### Endpoint dan UI
- `GET/POST /admin-tools/odoo-connection/` (`admin_odoo_connection`): halaman pengaturan dan Test Connection.
- Kartu menu ditampilkan pada dashboard Administrasi.
- Akses dilindungi decorator `_admin_only`; hanya Administrator/superuser.
- Form menampilkan URL, database, user integrasi, dan input API Key. API Key tidak diisi kembali pada GET; kolom kosong berarti pertahankan key lama.

### Enkripsi dan konfigurasi server
- Paket runtime: `requests` dan `cryptography`.
- Kunci Fernet dibaca dari environment `ODOO_API_ENCRYPTION_KEY`, diteruskan oleh Docker Compose dari file `.env`.
- Buat kunci di lingkungan tepercaya dengan `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`, lalu simpan sebagai `ODOO_API_ENCRYPTION_KEY=...` di file `.env` server. Jangan commit nilai kunci ke Git.
- Kunci harus stabil dan dicadangkan secara aman. Jika hilang/berubah, API Key terenkripsi yang sudah tersimpan tidak dapat didekripsi; masukkan ulang API Key setelah memulihkan konfigurasi kunci.
- Jika environment key tidak tersedia/tidak valid, penyimpanan API Key ditolak.

### Protokol Test Connection
- Kirim `POST {base_url}/json/2/res.users/context_get` dengan JSON body kosong, `Authorization: bearer <API_KEY>`, `Content-Type: application/json`, dan `User-Agent`.
- Tambahkan `X-Odoo-Database` jika database diisi.
- Timeout koneksi/read dibatasi; redirect dinonaktifkan; HTTPS diwajibkan kecuali localhost/127.0.0.1.
- HTTP 200 menandakan endpoint berhasil memvalidasi key dan mengembalikan context user. Ini bukan bukti bahwa seluruh model/operasi yang kelak dibutuhkan integrasi memiliki permission.
- 401/403 ditampilkan sebagai penolakan autentikasi/akses; 404 sebagai endpoint tidak ditemukan; error jaringan dan respons lain dicatat sebagai gagal tanpa menampilkan API Key.
- Pemanggilan `res.users/context_get` tanpa ID merupakan cara yang didokumentasikan Odoo 19 untuk mengambil context/current user dari API Key.

### Batas lingkup dan verifikasi
Tahap ini tidak melakukan sinkronisasi, pembacaan master, atau transaksi RO. Belum ada bukti koneksi ke instance Odoo pengguna, build Docker, migration apply, maupun pengujian browser. Validasi deployment perlu memastikan environment key terpasang, migration 0008 berjalan, halaman hanya dapat diakses Administrator, dan Test Connection berhasil dengan API Key yang valid.
**Persyaratan lisensi Odoo:** Dokumentasi Odoo 19 menyatakan External JSON-2 API hanya tersedia pada paket Custom dan tidak tersedia pada One App Free atau Standard. Kegagalan koneksi pada paket yang tidak mendukung API bukan kesalahan API Key aplikasi.

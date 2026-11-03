# Product Requirements Document (PRD)
## Aplikasi Master Data (RO)

| Atribut | Nilai |
|---|---|
| Produk | Aplikasi Master Data |
| Repository | `xsigerproject-cyber/RO` |
| Branch acuan | `main` |
| Status dokumen | Baseline berdasarkan implementasi repository |
| Tanggal | 3 November 2026 |

## Dokumen Terkait

Alasan dan konteks historis di balik aturan bisnis dicatat pada [`doc/DECISION_LOG.md`](DECISION_LOG.md). PRD ini tetap menjadi rujukan kebutuhan dan aturan bisnis yang berlaku.

## 1. Ringkasan Produk

Aplikasi Master Data adalah aplikasi web internal untuk mengelola data referensi operasional yang terdiri dari Dapur, Jadwal, Toko, dan Template Produk. Aplikasi dibangun menggunakan Django, PostgreSQL, Docker Compose, dan Bootstrap 5.

Dokumen ini mendeskripsikan kebutuhan yang tercermin pada kode repository saat ini. Dokumen tidak menganggap fitur yang belum terlihat pada implementasi sebagai fitur yang sudah tersedia.

## 2. Latar Belakang dan Masalah

Data master perlu disimpan secara terpusat agar pengguna dapat melihat, mencari, menambah, mengubah, menghapus sesuai hak akses, serta memindahkan data melalui berkas Excel. Template Produk memiliki hubungan ke Master Dapur sehingga kode dapur harus merujuk ke data Dapur yang tersedia.

## 3. Tujuan Produk

1. Menyediakan satu aplikasi web untuk pengelolaan empat kelompok data master.
2. Menjaga konsistensi relasi Template Produk ke Dapur.
3. Menyediakan pencarian, dashboard ringkas, impor, dan ekspor Excel.
4. Membatasi tindakan pengguna berdasarkan peran.
5. Menyediakan data awal untuk instalasi database baru melalui migration.

## 4. Pengguna dan Hak Akses

Aplikasi menggunakan autentikasi Django. Kode pemeriksaan hak akses mengenali grup berikut:

| Peran/grup | Lihat | Tambah | Ubah | Hapus |
|---|---:|---:|---:|---:|
| Admin Master | Ya | Ya | Ya | Ya |
| Editor Master | Ya | Ya | Ya | Tidak |
| Viewer Master | Ya | Tidak | Tidak | Tidak |
| Superuser | Ya | Ya | Ya | Ya |

Catatan implementasi:
- Fungsi `can_manage` memberikan izin kelola kepada superuser, Admin Master, dan Editor Master.
- Fungsi `can_delete` hanya memberikan izin hapus kepada superuser dan Admin Master.
- Akses menu/halaman data memerlukan login.
- Grup dan keanggotaan pengguna dikelola melalui Django Admin; repository yang ditinjau belum menunjukkan otomasi pembuatan grup tersebut.

## 5. Ruang Lingkup Fungsional

### 5.1 Dashboard
- Menampilkan jumlah record untuk Dapur, Jadwal, Toko, dan Produk.
- Menyediakan tautan menuju daftar masing-masing master.

### 5.2 Pengelolaan Master Dapur
Field:
- `kode_dapur`: primary key numerik.
- `nama_dapur`: nama dapur.
- `operation_type`: jenis operasi.
- `document`: kode dokumen.

Pengguna yang berhak dapat menambah dan mengubah data. Penghapusan hanya untuk Admin Master/superuser.

### 5.3 Pengelolaan Master Jadwal
Field:
- `kode_jadwal`: primary key numerik.
- `jadwal_kirim`: deskripsi jadwal pengiriman.

### 5.4 Pengelolaan Master Toko
Field:
- `kode_toko`: primary key numerik.
- `nama_toko`: nama toko.

### 5.5 Pengelolaan Master Template Produk
Field:
- `kode_produk`: primary key numerik.
- `nama_produk`: nama produk.
- `dapur`: foreign key ke Master Dapur.

Relasi Dapur menggunakan kebijakan `PROTECT`, sehingga Dapur yang masih direferensikan produk tidak dapat dihapus.

### 5.6 Pencarian
- Daftar master menyediakan parameter pencarian `q`.
- Pencarian dilakukan pada field teks yang tersedia.
- Untuk Template Produk, pencarian juga mencakup nama dan kode Dapur terkait.
- Field kode numerik dicari sebagai angka eksak.

### 5.7 Impor Excel
- Format berkas: `.xlsx`.
- Ukuran maksimum: 5 MB.
- Header wajib mengikuti nama field yang ditentukan.
- Data divalidasi menggunakan Django ModelForm.
- Seluruh proses impor berada dalam transaksi database; kesalahan validasi membatalkan transaksi.
- Primary key wajib diisi dan berupa bilangan bulat.
- Untuk Template Produk, kolom `kode_dapur` harus mengacu ke Dapur yang ada.
- Jika primary key sudah ada, record tersebut diperbarui; jika belum ada, record dibuat.
- Pengguna harus memiliki hak kelola.

Header yang diterima:

| Master | Header Excel |
|---|---|
| Dapur | `kode_dapur,nama_dapur,operation_type,document` |
| Jadwal | `kode_jadwal,jadwal_kirim` |
| Toko | `kode_toko,nama_toko` |
| Template Produk | `kode_produk,nama_produk,kode_dapur` |

### 5.8 Template Import Excel
- Template menyediakan header sesuai master yang dipilih.
- Jika tabel memiliki data, baris contoh diambil dari record pertama berdasarkan primary key terkecil.
- Untuk Template Produk, nilai `kode_dapur` diambil dari relasi record contoh.
- Jika tabel kosong, template hanya berisi header.
- Baris contoh diberi format visual berbeda dan komentar penjelasan.
- Baris contoh adalah data nyata dari database, bukan data dummy. Jika diimpor tanpa perubahan, perilaku upsert berdasarkan primary key akan memperbarui record yang sama.

### 5.9 Ekspor Excel
- Pengguna yang sudah login dapat mengunduh seluruh data pada master yang dipilih dalam format `.xlsx`.
- Untuk Template Produk, kolom relasi diekspor sebagai `kode_dapur`.

### 5.10 Preferensi Tema
- Pengguna yang login dapat menyimpan tema: Light, Dark, Ocean, Forest, atau Sunset.
- Preferensi disimpan pada model UserProfile dan digunakan pada tampilan dasar aplikasi.

### 5.11 Data Awal (Seed Data)
Migration `0003_seed_master_data` memasukkan data awal berikut pada database yang menjalankan migration tersebut:

**Dapur**

| Kode | Nama | Operation Type | Document |
|---:|---|---|---|
| 10 | Dapur Cake | Order Cake | CAKE |
| 12 | Dapur Cake Slice | Order Cake Slice | CAKESL |
| 13 | Dapur Pastry | Order Pastry | PASTRY |
| 14 | Dapur Jajan Pasar | Order Jajan Pasar | JJP |
| 15 | Dapur Roti | Order Roti | ROTI |
| 16 | Dapur Sultan | Order Sultan | SUL |

**Jadwal**

| Kode | Jadwal Kirim |
|---:|---|
| 10 | Pagi - Subuh |
| 12 | Pagi - 10.00 WIB |
| 13 | Siang - 13.00 WIB |

**Toko**

| Kode | Nama |
|---:|---|
| 10 | Toko Sudirman |
| 12 | Toko Kedaton |
| 13 | Toko Unila |
| 14 | Toko RSAM |
| 15 | Toko Metro |
| 16 | Toko RS Airan |

**Template Produk**

| Kode | Nama Produk | Kode Dapur |
|---:|---|---:|
| 10001 | Roti Manis | 15 |
| 10002 | Roti Coklat | 15 |
| 10003 | Roti Kelapa | 15 |
| 10004 | Roti Kopi | 15 |
| 10005 | Arem Arem Sultan | 14 |
| 10006 | Sosis Solo | 14 |

Migration menggunakan `update_or_create` berdasarkan primary key untuk menghindari duplikasi saat seed dijalankan. Migration seed dijalankan melalui mekanisme `manage.py migrate`; tidak perlu memasukkan record secara manual.

## 6. Kebutuhan Non-Fungsional

- **Keamanan akses:** halaman master memerlukan login; operasi tulis/hapus memeriksa hak akses di sisi server.
- **Validasi:** data form dan impor divalidasi oleh Django.
- **Konsistensi data:** relasi produk-dapur dijaga oleh foreign key dan `PROTECT`.
- **Integritas impor:** impor dibungkus transaksi atomik.
- **Deployment:** aplikasi dijalankan dalam container Docker dan menggunakan PostgreSQL 16.
- **Static files:** static assets dikumpulkan saat container web start dan dilayani melalui WhiteNoise.
- **Bahasa/waktu:** konfigurasi Django menggunakan `id-id`, `Asia/Jakarta`, dan timezone aktif.

## 7. Di Luar Ruang Lingkup / Belum Terdefinisi

Hal berikut tidak dapat dipastikan sebagai kebutuhan/fitur tersedia dari kode yang ditinjau:
- Workflow persetujuan perubahan data.
- Audit trail/histori perubahan per record.
- Soft delete dan pemulihan data.
- API publik atau integrasi dengan sistem lain.
- Pagination dan batas jumlah record pada daftar.
- Backup terjadwal dan disaster recovery.
- Notifikasi.
- Pengelolaan grup/role otomatis di luar Django Admin.

## 8. Kriteria Penerimaan

1. Pengguna terautentikasi dapat membuka dashboard dan empat daftar master.
2. Dashboard menampilkan jumlah record yang sesuai database.
3. Form Dapur, Jadwal, Toko, dan Template Produk menerima data valid dan menolak data tidak valid.
4. Produk hanya dapat disimpan dengan Dapur yang valid.
5. Viewer tidak dapat melakukan operasi tambah/ubah/hapus.
6. Editor dapat tambah/ubah tetapi tidak dapat menghapus.
7. Admin Master/superuser dapat tambah/ubah/hapus.
8. Pencarian menghasilkan record yang cocok dengan aturan pencarian.
9. Ekspor menghasilkan file XLSX dengan header dan nilai yang benar.
10. Impor XLSX memvalidasi header, ukuran, ekstensi, primary key, dan relasi; kegagalan tidak menyisakan impor parsial.
11. Template import menggunakan record pertama berdasarkan primary key terkecil, atau hanya header bila tabel kosong.
12. Migration seed menghasilkan 6 Dapur, 3 Jadwal, 6 Toko, dan 6 Template Produk pada database baru.

## 9. Risiko dan Catatan

- Migration seed menggunakan primary key yang telah ditentukan. Jika database sudah memiliki record dengan kode yang sama, nilai field record tersebut akan diperbarui oleh migration.
- Backup database disarankan sebelum deployment migration pada database produksi.
- Keberhasilan dokumen ini tidak menyatakan bahwa seluruh skenario telah diuji pada server produksi.


## 10. Status Aktif/Nonaktif Template Produk dan Sinkronisasi Draft

- Setiap Template Produk memiliki status Aktif/Nonaktif; produk baru secara default berstatus Aktif.
- Hanya produk Aktif pada Dapur yang dipilih yang dimasukkan ke transaksi RO baru.
- Draft yang masih berjalan disinkronkan dengan Template Produk Aktif setiap kali transaksi Draft dibuka atau disimpan:
  - Produk yang berubah menjadi Nonaktif otomatis dikeluarkan dari Draft beserta Qty Draft-nya.
  - Produk Aktif yang baru ditambahkan ke Template Produk ikut ditambahkan ke Draft dengan Qty awal 0.
  - Produk yang tetap Aktif mempertahankan Qty yang sudah diinput.
- Perubahan status Template Produk tidak mengubah RO berstatus Terkirim.
- Produk musiman dapat digunakan kembali dengan mengaktifkan kembali record Template Produk yang sama; tidak perlu membuat kode produk baru.
- Status aktif/nonaktif dikelola oleh pengguna yang memiliki hak kelola master.

Kriteria penerimaan tambahan:
13. Template Produk dapat disimpan sebagai Aktif atau Nonaktif.
14. RO baru hanya menampilkan produk Aktif dari Dapur terpilih.
15. Draft menghapus produk Nonaktif dan Qty-nya saat Draft dibuka atau disimpan.
16. Draft menambahkan produk Aktif baru dengan Qty 0 tanpa mereset Qty produk lain.
17. Perubahan status Template Produk tidak mengubah baris RO Terkirim.


## 11. Administrasi Data dan Inisialisasi Data Testing (Rencana)

<badge>Belum diimplementasikan</badge>

Fitur ini khusus untuk Administrator. Tujuannya membersihkan data uji sebelum pengisian data resmi dan Go-Live, tanpa menghapus master operasional yang diperlukan aplikasi.

### 11.1 Penghapusan Template Produk

Administrator dapat menghapus satu Template Produk, seluruh Template Produk pada satu Dapur, atau seluruh isi Template Produk. Sistem harus menampilkan cakupan dan jumlah record yang akan dihapus.

Karena Template Produk dapat direferensikan oleh baris RO, penghapusan selektif hanya boleh dilakukan jika produk yang dituju tidak direferensikan oleh RO mana pun. Jika masih direferensikan, sistem menolak tindakan dan memberi tahu Administrator bahwa data RO terkait perlu dibersihkan terlebih dahulu. Sistem tidak boleh menghapus RO secara diam-diam sebagai efek samping penghapusan Template Produk.

### 11.2 Inisialisasi Data Testing

Sediakan tindakan terpisah **Inisialisasi Data Testing** untuk mengosongkan seluruh data RO (Draft maupun Terkirim) dan seluruh Template Produk (Aktif maupun Nonaktif).

Inisialisasi harus mempertahankan:
- Master Dapur, Jadwal, dan Toko.
- Akun pengguna, grup/peran, permission, dan preferensi pengguna.
- Konfigurasi aplikasi, migration history, serta log audit yang memang harus dipertahankan.

Inisialisasi tidak menghapus volume/database PostgreSQL dan tidak mereset sequence/auto-increment kecuali ada keputusan terpisah yang disetujui.

### 11.3 Pengamanan Wajib

- Semua endpoint dan tindakan diperiksa di sisi server menggunakan izin khusus Administrator. Admin Master/Editor Master tidak otomatis memperoleh akses ini; superuser dapat memperoleh akses sebagai Administrator.
- Menu dan tombol hanya ditampilkan kepada Administrator, tetapi penyembunyian menu bukan pengganti pemeriksaan izin server-side.
- Mutasi hanya menerima POST dan dilindungi CSRF.
- Tampilkan ringkasan jumlah RO dan Template Produk yang akan dihapus.
- Untuk inisialisasi, minta Administrator mengetik teks persis `RESET DATA` dan mengonfirmasi bahwa tindakan tidak dapat dibatalkan dari aplikasi.
- Proses inisialisasi harus atomik: hapus baris RO terlebih dahulu, lalu Template Produk, dalam satu transaksi database. Jika salah satu langkah gagal, seluruh transaksi dibatalkan.
- Catat pelaku, waktu, jenis tindakan, dan jumlah record yang dihapus pada log audit yang tidak ikut dihapus.
- Administrator wajib membuat backup PostgreSQL yang dapat dipulihkan sebelum inisialisasi. Ekspor Excel bukan pengganti backup database penuh.

### 11.4 Alur Operasional yang Disarankan

1. Selesaikan pengujian aplikasi dan pastikan data uji tidak lagi diperlukan.
2. Buat dan verifikasi backup PostgreSQL.
3. Jalankan Inisialisasi Data Testing sebagai Administrator.
4. Impor Template Produk resmi.
5. Verifikasi jumlah, kode produk, Dapur, dan status Aktif/Nonaktif.
6. Lanjutkan Go-Live setelah hasil verifikasi disetujui.

### 11.5 Kriteria Penerimaan Fitur (Saat Diimplementasikan)

18. Hanya Administrator/superuser yang dapat melihat dan menjalankan menu administrasi data; role lain menerima HTTP 403 jika mencoba endpoint secara langsung.
19. Administrator dapat menghapus satu Template Produk, seluruh Template Produk pada Dapur terpilih, atau seluruh Template Produk jika tidak ada referensi RO.
20. Penghapusan Template Produk yang masih direferensikan RO ditolak dan tidak mengubah RO maupun Template Produk lain.
21. Konfirmasi menampilkan cakupan dan jumlah record yang akan dihapus.
22. Inisialisasi menghapus semua RO Draft dan Terkirim serta semua Template Produk dalam satu transaksi atomik.
23. Inisialisasi mempertahankan Dapur, Jadwal, Toko, akun, grup/peran, permission, konfigurasi, dan log audit yang ditetapkan untuk dipertahankan.
24. Inisialisasi memerlukan konfirmasi teks `RESET DATA`; konfirmasi yang salah tidak mengubah data.
25. Log audit mencatat pelaku, waktu, jenis tindakan, dan jumlah record yang dihapus.
26. Kegagalan di tengah proses inisialisasi menyebabkan rollback penuh.


## 12. Modul Administrasi User dan Database

<badge>Implementasi awal pada branch main; wajib diverifikasi sebelum produksi</badge>

Modul Administrasi hanya dapat diakses Administrator dan superuser.

### 12.1 Manajemen User
- Menampilkan daftar user, status aktif, dan grup/role.
- Membuat user dengan username, nama, email, status aktif, grup/role, serta Toko jika role Admin Toko.
- User baru dibuat tanpa password yang dapat digunakan; Administrator harus menetapkan password melalui aksi Ganti Password.
- Mengubah data user, role, status aktif, dan relasi Toko untuk Admin Toko.
- Menghapus user melalui POST dengan konfirmasi.
- Mengatur password baru untuk user dengan validasi password Django.
- Akun yang sedang digunakan tidak dapat dihapus atau dinonaktifkan sendiri.
- Superuser tidak dapat dihapus melalui modul ini; pengubahan akun superuser dan password-nya hanya boleh dilakukan oleh superuser.
- Administrator aktif terakhir tidak boleh dinonaktifkan, kehilangan role Administrator, atau dihapus.

### 12.2 Backup Database
- Menjalankan `pg_dump` dalam format custom PostgreSQL.
- Menyimpan file pada named volume Docker terpisah bernama `db_backups`, bukan pada volume data PostgreSQL.
- Menampilkan daftar file backup dan menyediakan unduhan.
- Backup harus disalin ke media/lokasi terpisah untuk perlindungan terhadap kerusakan server atau volume.

### 12.3 Restore Database
- Hanya menerima file custom dump berekstensi `.dump`, maksimum 1 GB.
- Memvalidasi arsip menggunakan `pg_restore --list`.
- Memerlukan teks konfirmasi persis `RESTORE DATABASE`.
- Sebelum restore, sistem otomatis membuat backup database aktif.
- Restore memakai `pg_restore` dengan clean/if-exists, no-owner/no-privileges, exit-on-error, dan single-transaction.
- Jika restore gagal, transaksi restore dibatalkan; backup kondisi sebelum restore tetap tersedia.
- Restore mengganti isi database aktif. Pengguna lain harus menghentikan aktivitas aplikasi selama proses berlangsung.

### 12.4 Batasan Operasional
- Backup dan restore memerlukan PostgreSQL client tools (`pg_dump` dan `pg_restore`) di image web.
- File backup yang tersimpan pada volume Docker di server yang sama bukan pengganti salinan off-site.
- Restore dapat mengubah user, password, RO, master data, dan seluruh isi database sesuai kondisi pada backup.
- Restore tidak menjamin pemulihan database jika file backup rusak; prosedur backup harus diuji dengan restore pada lingkungan non-produksi.
- Fitur ini belum boleh digunakan pada produksi sebelum uji backup, restore, hak akses, dan pemulihan selesai.

### 12.5 Kriteria Penerimaan
27. Hanya Administrator/superuser dapat mengakses seluruh endpoint modul Administrasi.
28. Administrator dapat membuat, melihat, mengubah, dan menghapus user non-superuser.
29. Role Admin Toko memerlukan pemetaan Toko; role lain tidak menyimpan pemetaan Toko.
30. User baru tidak memiliki password aktif sampai Administrator menetapkan password.
31. Password baru divalidasi dan disimpan menggunakan mekanisme hash Django.
32. Akun sendiri dan Administrator aktif terakhir dilindungi dari penghapusan/penonaktifan yang dapat mengunci akses administrasi.
33. Backup menghasilkan file PostgreSQL custom dump yang tidak kosong dan dapat diunduh.
34. File backup disimpan pada volume terpisah dari volume data database.
35. Restore menolak ekstensi/arsip/konfirmasi yang tidak valid dan ukuran file di atas batas.
36. Restore otomatis membuat backup sebelum memulai proses pemulihan.
37. Restore menggunakan transaksi tunggal dan gagal tanpa meninggalkan pemulihan parsial.


## 13. Manajemen Role / Group (Implementasi awal)

Modul Administrasi menyediakan menu Manajemen Role untuk Administrator dan superuser.

- Menampilkan daftar Group, jumlah user yang tergabung, dan jumlah permission.
- Administrator dapat membuat Group baru dan memilih permission Django yang akan diberikan.
- Administrator dapat mengubah nama Group non-inti dan mengatur permission Group.
- Group yang masih digunakan oleh satu atau lebih user tidak dapat dihapus. Administrator harus melepas Group dari semua user terlebih dahulu.
- Role inti `Administrator`, `Admin Toko`, dan `Admin Produksi` tidak dapat dihapus atau diganti namanya karena nama tersebut digunakan langsung oleh pemeriksaan hak akses aplikasi. Permission pada role inti tetap dapat diatur.
- Seluruh halaman dan aksi dibatasi server-side untuk Administrator/superuser; penghapusan hanya menerima POST dan dilindungi CSRF.

Kriteria penerimaan tambahan:
38. Administrator dapat melihat daftar role, jumlah user, dan jumlah permission setiap role.
39. Administrator dapat membuat role dengan nama unik dan permission pilihan.
40. Administrator dapat mengubah nama role non-inti dan permission role.
41. Penghapusan role yang masih memiliki user ditolak tanpa mengubah data.
42. Role inti tidak dapat dihapus atau diganti nama, tetapi permission-nya dapat dikelola.
43. Pengguna non-Administrator menerima HTTP 403 pada endpoint Manajemen Role.


### 13.1 Filter Permission saat mengubah Role
- Form Ubah Role menyediakan kotak filter kata kunci untuk mempersempit daftar permission yang tampil.
- Pencarian tidak membedakan huruf besar/kecil dan mencocokkan nama permission, nama model, nama aplikasi, serta codename.
- Contoh kata kunci `view` menampilkan permission yang mengandung kata tersebut.
- Filter hanya menyembunyikan/menampilkan pilihan di browser; pilihan checkbox yang sudah dicentang tetap dipertahankan saat filter berubah.


### 13.2 Tombol penerapan filter permission
- Filter permission tidak diterapkan otomatis saat pengguna mengetik.
- Administrator mengetik kata kunci lalu menekan tombol **Filter** untuk menampilkan permission yang cocok.
- Tombol **Bersihkan** menghapus kata kunci dan menampilkan kembali seluruh permission.
- Tombol Enter pada kolom filter menjalankan aksi Filter.
- Status checkbox permission yang sudah dipilih tetap dipertahankan saat daftar disaring.

### 12.6 Perbaikan penyimpanan grup saat Tambah User
- Saat `ModelForm.save(commit=True)` dipanggil, Django sudah menyimpan relasi many-to-many `groups`; aplikasi tidak boleh memanggil `save_m2m()` lagi karena method itu hanya tersedia pada alur `save(commit=False)`.
- Pembuatan user tetap menyimpan pemetaan Toko pada `UserProfile` dan tetap membuat password awal unusable sampai Administrator menetapkan password.
- Kriteria penerimaan: POST Tambah User dengan role dan Toko yang valid berhasil membuat user, menyimpan grup yang dipilih, serta menyimpan pemetaan Toko tanpa `AttributeError`.

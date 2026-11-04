# Decision Log dan Rekonstruksi Riwayat Percakapan RO

| Atribut | Nilai |
|---|---|
| Repository | `xsigerproject-cyber/RO` |
| Branch | `main` |
| Jenis | Rekonstruksi keputusan dan alasan |
| Tanggal | 3 November 2026 |

## 1. Tujuan dan batas akurasi

Dokumen ini mencatat **mengapa** aturan bisnis dipilih agar pengembangan dapat diteruskan ketika konteks chat tidak tersedia. Dokumen ini melengkapi:
- `doc/PRD.md`: kebutuhan bisnis, aturan proses, hak akses, kriteria penerimaan.
- `doc/DDS.md`: desain teknis dan implementasi yang tercermin pada source code.

Catatan ini merupakan **rekonstruksi ringkasan percakapan/keputusan, bukan transkrip verbatim**. Redaksi dirapikan dan hanya memuat konteks yang tersedia. Jangan menganggap roadmap sebagai fitur yang sudah selesai atau catatan sebagai bukti pengujian produksi.

## 2. Latar belakang masalah

- Aplikasi RO merupakan alat internal untuk menyiapkan, memvalidasi, dan mengonsolidasikan data sebelum diunggah ke Odoo 19 Manufacturing; bukan pengganti Odoo.
- Proses persiapan dan upload manual membebani Admin Produksi. Estimasi yang disampaikan: sekitar 30 menit per toko; lima toko dapat memerlukan sekitar 2,5 jam.
- Tujuan pengembangan adalah mengurangi pekerjaan berulang, menjaga konsistensi, dan menyiapkan file Excel untuk upload Odoo.
- Format dan mapping Excel Odoo harus mengikuti contoh/template Odoo 19 yang disetujui. Jangan mengarang format import.

## 3. Keputusan bisnis dan alasan

### 3.1 Template Produk sebagai whitelist

**Konteks:** Odoo memiliki sekitar 6.000 SKU, sedangkan produk yang aktif diproduksi sekitar 600–700. Admin Toko tidak perlu mencari dari seluruh SKU.

**Keputusan:** Template Produk adalah daftar definitif produk yang boleh dipesan, dikelompokkan berdasarkan Dapur. Setelah memilih Dapur, Admin Toko melihat daftar produk terkait dan mengisi Qty.

**Alasan:** membatasi pilihan pada produk operasional, mengurangi salah pilih SKU, dan menyederhanakan input. Pencarian ke seluruh katalog Odoo tidak diperlukan dalam alur input yang dibahas.

### 3.2 Aktif/Nonaktif, bukan menghapus produk musiman

**Konteks:** produk musiman dapat berhenti sementara lalu digunakan kembali.

**Keputusan:** Template Produk memiliki status Aktif/Nonaktif; produk baru default Aktif. Produk Nonaktif tidak ditawarkan untuk RO baru. Produk musiman diaktifkan kembali dengan record/kode yang sama.

**Alasan:** master dan identitas SKU tetap terjaga tanpa membuat ulang record.

### 3.3 Sinkronisasi Draft dengan Template Produk Aktif

**Keputusan yang disetujui:**
- Produk yang tetap Aktif mempertahankan Qty Draft.
- Produk yang berubah menjadi Nonaktif dihapus dari Draft dan Qty-nya ikut dibuang.
- Produk Aktif yang baru ditambahkan masuk ke Draft dengan Qty 0.
- Perubahan Template Produk tidak mengubah RO berstatus Terkirim.

**Alasan:** Draft harus mengikuti whitelist terbaru tanpa mereset Qty yang masih valid; RO Terkirim harus tetap menjadi rekam transaksi yang tidak berubah karena perubahan master.

### 3.4 Kunci transaksi RO

Satu transaksi dikenali oleh kombinasi **Tanggal RO + Kode Toko + Kode Dapur + Kode Jadwal**. Jika Draft dengan kombinasi yang sama sudah ada, Draft tersebut dibuka kembali beserta produk dan Qty-nya, bukan membuat transaksi duplikat.

**Alasan:** mencegah duplikasi transaksi untuk kombinasi operasional yang sama.

### 3.5 Draft dan Kirim

**Keputusan:**
- Status transaksi: Draft atau Terkirim.
- Draft menyimpan seluruh baris produk relevan, termasuk Qty 0.
- Saat Kirim, baris Qty kurang dari 1 dihapus.
- Kirim mensyaratkan setidaknya satu Qty minimal 1.
- Setelah Terkirim, Admin Toko tidak dapat mengubah transaksi.
- Perubahan status Template Produk tidak mengubah baris Terkirim.

**Alasan:** Draft adalah ruang kerja sebelum kuantitas final; transaksi terkirim hanya memuat produk yang benar-benar dipesan dan harus tetap terjaga.

### 3.6 Hak akses RO

- **Admin Toko:** input RO untuk toko yang ditugaskan kepadanya; tidak boleh mengakses/mengubah RO toko lain.
- **Admin Produksi:** dapat melihat RO seluruh toko.
- **Administrator:** akses penuh termasuk konfigurasi, master data, dan pengguna.

**Rencana lanjutan:** Admin Produksi diharapkan dapat mengubah Qty pada RO Terkirim sebelum konsolidasi. Batas status/waktu, audit perubahan, dan aturan rinci harus ditetapkan sebelum implementasi; jangan menganggap fitur ini sudah tersedia.

### 3.7 Kunci konsolidasi produksi

Qty lintas toko hanya dijumlahkan jika seluruh dimensi ini sama:
1. Tanggal Produksi
2. Dapur
3. Jadwal Produksi
4. Produk

**Alasan:** produk yang sama tidak boleh digabung jika tanggal, dapur, atau jadwal produksinya berbeda.

Tanggal Produksi direncanakan diisi Admin Produksi pada tahap berikutnya, bukan saat Admin Toko membuat RO. Workflow penetapan tanggal dan status konsolidasi masih perlu dirinci dalam PRD.

## 4. Arah pengembangan yang pernah dibahas

Roadmap yang pernah dijelaskan:
1. Input RO dan Qty per toko.
2. Validasi data RO.
3. Konsolidasi berdasarkan Tanggal Produksi, Dapur, Jadwal Produksi, dan Produk.
4. Beberapa format Excel untuk upload Odoo berdasarkan template dan logika pivot yang benar.
5. Rekap produksi per Produk dan Dapur.
6. Riwayat ekspor.

Ini adalah arah pengembangan, bukan klaim bahwa seluruh fitur telah diimplementasikan.

## 5. Prinsip kerja pengembangan

1. Baca PRD, DDS/DDL, source code, dan migration sebelum mengubah aplikasi.
2. PRD adalah rujukan kebutuhan bisnis; DDS/DDL adalah rujukan teknis/database; dokumen ini menjelaskan alasan di balik keputusan.
3. Perubahan kebutuhan harus dicatat di PRD dan keputusan; perubahan teknis/database dicatat di DDS/DDL.
4. Periksa konsistensi dokumen, kode, dan migration setelah perubahan.
5. Jangan menyatakan test atau deployment berhasil tanpa bukti.
6. Update rutin server menggunakan `git pull origin main` dan `docker compose up -d --build`; entrypoint menjalankan migration sesuai desain saat container start.
7. Database memakai volume persisten. Jangan gunakan `docker compose down -v` sebagai update rutin karena dapat menghapus data.
8. Backup database sebelum migration produksi.

## 6. Jejak implementasi yang tercatat

Perubahan Template Produk Aktif/Nonaktif yang tercatat:
- Menambahkan `TemplateProduk.is_active`, default `True`.
- Menambahkan status pada konfigurasi form/master dan label status pada daftar.
- Menambahkan sinkronisasi Draft berdasarkan Template Produk Aktif.
- Memperbarui PRD dan DDS untuk aturan tersebut.
- Migration field terakhir tercatat sebagai `0006_templateproduk_is_active.py`.

**Perlu verifikasi:** riwayat perubahan nomor migration pernah mengalami penataan dan potensi dependency yang tidak sesuai. Sebelum deployment, periksa semua file migration pada branch `main`, dependency-nya, dan status database target. Jangan menganggap migration siap hanya berdasarkan nomor yang tercatat di sini.

## 7. Hal yang belum boleh diasumsikan

- Semua roadmap sudah diimplementasikan.
- Admin Produksi sudah dapat mengubah Qty setelah RO Terkirim.
- Konsolidasi dan ekspor Odoo sudah berjalan.
- Format upload Odoo sudah final tanpa template yang disetujui.
- Migration atau test sudah berhasil di server produksi.
- Audit trail, notifikasi, dan seluruh validasi tambahan sudah ditetapkan.

## 8. Format pencatatan keputusan berikutnya

### YYYY-MM-DD — Judul keputusan
- **Konteks/masalah:**
- **Pilihan yang dibahas:**
- **Keputusan yang disetujui:**
- **Alasan:**
- **Dampak PRD:**
- **Dampak DDS/DDL/database:**
- **Dampak kode/migration:**
- **Status implementasi dan pengujian:**
- **Referensi commit:**

---

Jika konteks percakapan hilang, mulai dengan membaca dokumen ini, `doc/PRD.md`, `doc/DDS.md`, lalu periksa source code dan migration pada branch aktif. Keputusan eksplisit terbaru tetap menjadi acuan.


## 9. 2026-11-03 — Pembersihan data testing oleh Administrator sebelum Go-Live

**Konteks/masalah:**
Data Template Produk dan RO yang digunakan selama pengembangan/pengujian nantinya perlu dibersihkan sebelum data resmi dimasukkan dan aplikasi digunakan secara operasional. Penghapusan Template Produk secara langsung berisiko melanggar relasi karena produk dapat direferensikan oleh baris RO.

**Pilihan yang dibahas:**
- Penghapusan Template Produk berdasarkan satu produk, satu Dapur, atau seluruh Template Produk.
- Inisialisasi yang mengosongkan RO dan Template Produk sekaligus.
- Penghapusan manual langsung dari database.

**Keputusan yang disetujui:**
1. Sediakan area Administrasi Data khusus Administrator.
2. Administrator dapat menghapus satu Template Produk, seluruh Template Produk pada Dapur terpilih, atau seluruh Template Produk.
3. Penghapusan selektif hanya boleh dilakukan jika target tidak direferensikan oleh RO. Jika masih direferensikan, tindakan ditolak; sistem tidak boleh menghapus RO diam-diam.
4. Sediakan tindakan terpisah Inisialisasi Data Testing yang menghapus seluruh RO (Draft dan Terkirim) serta seluruh Template Produk.
5. Inisialisasi mempertahankan Dapur, Jadwal, Toko, akun pengguna, grup/peran, permission, UserProfile, konfigurasi aplikasi, migration history, dan log audit yang harus dipertahankan.
6. Penghapusan RO lalu Template Produk dilakukan dalam satu transaksi atomik. Kegagalan harus membatalkan seluruh proses.
7. Reset memerlukan konfirmasi mengetik `RESET DATA`, menampilkan jumlah data terdampak, dan mencatat pelaku/waktu/jenis tindakan/jumlah record pada audit log.
8. Backup PostgreSQL penuh yang dapat dipulihkan wajib dibuat sebelum reset. Ekspor Excel bukan backup database penuh.
9. Jangan menghapus database/volume Docker, menjalankan flush, atau mereset sequence secara otomatis.

**Alasan:**
Tujuannya membersihkan data uji sebelum Go-Live tanpa mengganggu master operasional, akun, dan konfigurasi. Pemisahan penghapusan selektif dan reset menyeluruh mengurangi risiko salah tindakan. Pemeriksaan referensi menjaga integritas RO, sedangkan transaksi atomik dan backup mengurangi risiko kehilangan data parsial/permanen.

**Dampak PRD:**
Menambahkan kebutuhan, batasan, pengamanan, alur pra-Go-Live, dan kriteria penerimaan untuk fitur Administrasi Data dan Inisialisasi Data Testing.

**Dampak DDS/DDL/database:**
Menambahkan rancangan otorisasi Administrator, pemeriksaan referensi RO, urutan hapus, transaksi atomik, data yang dipertahankan, audit, backup, dan pengujian. Belum menetapkan schema/model audit atau migration.

**Dampak kode/migration:**
Belum ada. Fitur ini dicatat sebagai rencana dan tidak boleh dianggap tersedia sebelum implementasi serta pengujian selesai.

**Status implementasi dan pengujian:**
Disetujui sebagai kebutuhan/rancangan tahap berikutnya; belum diimplementasikan dan belum diuji.

**Referensi commit:**
Diisi setelah perubahan dokumen ini tersimpan di repository.


## 10. 2026-11-03 — Modul Administrasi User, Backup, dan Restore Database

**Konteks/masalah:**
Administrator membutuhkan satu area untuk mengelola akun dan memelihara database tanpa bergantung pada Django Admin atau akses shell untuk pekerjaan rutin.

**Keputusan yang disetujui:**
1. Sediakan modul Administrasi yang hanya dapat diakses grup Administrator dan superuser.
2. Modul menyediakan CRUD user, pengaturan grup/role, status aktif, pemetaan Toko untuk Admin Toko, serta penggantian password user.
3. User baru dibuat dengan password unusable sampai Administrator menetapkan password.
4. Akun sendiri tidak dapat dihapus atau dinonaktifkan; superuser tidak dapat dihapus dari modul; superuser hanya dapat diubah oleh superuser.
5. Administrator aktif terakhir tidak boleh dihapus, dinonaktifkan, atau kehilangan role Administrator.
6. Backup database menggunakan PostgreSQL custom dump (`pg_dump -Fc`) dan disimpan pada named volume Docker terpisah dari volume database.
7. Restore menerima custom dump, mewajibkan konfirmasi `RESTORE DATABASE`, membuat backup otomatis sebelum restore, dan menjalankan `pg_restore` dalam single transaction.
8. Backup pada host yang sama bukan backup off-site; file backup perlu disalin ke lokasi terpisah.
9. Restore harus diuji di staging sebelum dipakai di produksi.

**Alasan:**
Pengelolaan user dan database merupakan fungsi administratif sensitif. Pemisahan akses, perlindungan akun administrator terakhir, backup otomatis sebelum restore, serta transaksi tunggal mengurangi risiko kehilangan akses dan kerusakan data parsial.

**Dampak PRD:**
Menambahkan kebutuhan manajemen user, backup, restore, pengamanan, batasan operasional, dan kriteria penerimaan.

**Dampak DDS/DDL/database:**
Menambahkan rancangan modul, endpoint, proses pg_dump/pg_restore, lokasi volume backup, otorisasi, dan daftar verifikasi. Tidak ada tabel database baru yang diperlukan untuk fungsi ini.

**Dampak kode/migration:**
Menambahkan `admin_forms.py`, `admin_views.py`, template `templates/admin_tools/`, endpoint `admin-tools/`, context processor menu Administrator, paket `postgresql16-client` pada image web, dan named volume `db_backups` pada Docker Compose. Tidak ada migration model baru.

**Status implementasi dan pengujian:**
Kode awal telah ditambahkan ke branch main. Belum ada bukti build Docker, pengujian Django, backup aktual, atau restore pada lingkungan target. Verifikasi runtime dan uji restore staging wajib dilakukan sebelum produksi.

**Referensi commit:**
Lihat riwayat commit branch `main` pada repository; perubahan dilakukan dalam beberapa commit bertahap.


## 11. 2026-11-03 — Perbaikan error halaman Tambah User

**Konteks/masalah:**
View `user_create` hanya mengembalikan template pada request POST. Saat form dibuka melalui GET, fungsi berakhir tanpa HTTP response sehingga Django dapat menghasilkan error server. Setelah POST valid, view juga belum mengarahkan pengguna kembali ke daftar user.

**Keputusan/perbaikan:**
1. Render form untuk request GET.
2. Jika POST tidak valid, render kembali form beserta error validasi.
3. Jika POST valid, simpan user, pertahankan aturan password awal unusable, tampilkan pesan sukses, lalu redirect ke daftar user.

**Dampak PRD:**
Tidak mengubah kebutuhan bisnis maupun aturan manajemen user.

**Dampak DDS/DDL:**
Mencatat alur GET, POST tidak valid, dan POST valid pada bagian modul administrasi.

**Dampak kode/migration:**
Memperbaiki fungsi `user_create` pada `masterdata/admin_views.py`. Tidak ada perubahan model atau migration.

**Status implementasi dan pengujian:**
Perbaikan kode telah dikomit ke branch main. Belum diuji pada server pengguna; verifikasi GET form, validasi POST, pembuatan user, serta pengaturan password tetap diperlukan.


## 12. 2026-11-03 — Penyelarasan frontend modul Administrasi

**Konteks/masalah:**
Tampilan form Tambah User memperlihatkan input native browser karena widget pada AdminUserForm belum diberi class Bootstrap. Layout role/grup juga belum disajikan sebagai pilihan yang mudah dibaca.

**Keputusan/perbaikan:**
Terapkan Bootstrap 5 secara konsisten pada field, gunakan grid responsif, checkbox role terstruktur, switch status aktif, dan rapikan heading/card pada halaman dashboard, user, password, backup, dan restore.

**Dampak PRD:** Tidak mengubah kebutuhan atau aturan bisnis.

**Dampak DDS/DDL:** Menambahkan catatan styling frontend pada bagian modul Administrasi.

**Dampak kode/migration:** Memperbarui `masterdata/admin_forms.py` dan template `templates/admin_tools/`. Tidak ada perubahan model atau migration.

**Status implementasi dan pengujian:** Perubahan tampilan telah dikomit ke branch main. Belum ada verifikasi visual pada browser/server pengguna.


## 13. 2026-11-03 — Manajemen Role / Group di modul Administrasi

**Konteks/masalah:**
Administrator sebelumnya hanya dapat memilih Group pada form user. Pembuatan dan pengelolaan Group masih harus dilakukan melalui Django Admin, sehingga alur administrasi belum terpusat.

**Keputusan:**
Tambahkan menu Manajemen Role di dashboard Administrasi. Administrator dapat membuat Group, mengubah Group, mengelola permission, melihat jumlah user dan permission, serta menghapus Group yang tidak sedang digunakan.

**Pengamanan dan kompatibilitas:**
- Semua endpoint hanya untuk Administrator/superuser.
- Penghapusan memakai POST + CSRF dan ditolak jika Group masih memiliki anggota.
- Nama role inti `Administrator`, `Admin Toko`, dan `Admin Produksi` tidak dapat diganti atau dihapus karena dipakai oleh logika akses aplikasi. Permission role inti tetap dapat dikelola.
- Tidak membuat atau mengubah model aplikasi; menggunakan Group dan Permission bawaan Django.

**Dampak PRD:** Menambahkan kebutuhan dan kriteria penerimaan Manajemen Role.

**Dampak DDS/DDL:** Menambahkan endpoint, form, view, dan aturan perlindungan role inti.

**Dampak kode/migration:** Menambah `masterdata/admin_role_forms.py`, dua template role, view dan route baru, serta kartu menu pada dashboard Administrasi. Tidak ada migration.

**Status implementasi dan pengujian:** Kode telah dikomit ke branch main. Belum diverifikasi pada server/browser dan belum ada klaim pengujian runtime.


## 14. 2026-11-03 — Filter kata kunci pada daftar permission Role

**Konteks/masalah:**
Daftar permission Django cukup panjang. Saat mengubah Role seperti Admin Produksi, Administrator perlu cara cepat menemukan permission berdasarkan kata seperti `view`.

**Keputusan:**
Tambahkan kotak filter kata kunci pada form Manajemen Role. Filter tidak case-sensitive dan mencari pada nama permission, model, app, serta codename. Contoh input `view` menampilkan seluruh pilihan yang mengandung kata tersebut.

**Perilaku penting:**
Filter hanya menyembunyikan pilihan yang tidak cocok; checkbox yang sudah terpilih tetap terpilih ketika filter berubah. Tombol Bersihkan mengembalikan semua permission.

**Dampak PRD/DDS:** Menambahkan kebutuhan dan catatan implementasi filter permission.

**Dampak kode/database:** Hanya mengubah template form Role. Tidak ada perubahan model atau migration.

**Status pengujian:** Belum diuji pada browser server pengguna.


## 15. 2026-11-03 — Tombol Filter eksplisit pada Manajemen Role

**Konteks/masalah:**
Pengguna menginginkan kontrol eksplisit untuk menerapkan kata kunci filter permission. Kolom pencarian yang langsung memfilter saat mengetik belum sesuai alur yang diharapkan.

**Keputusan:**
Sediakan tombol **Filter** yang menjalankan penyaringan setelah diklik. Enter pada kolom juga menjalankan filter. Tombol **Bersihkan** tetap tersedia untuk menampilkan kembali semua permission.

**Perilaku:** Checkbox yang telah dipilih tidak berubah ketika opsi disembunyikan atau ditampilkan. Filter mencocokkan label permission secara case-insensitive.

**Dampak PRD/DDS:** Memperjelas alur interaksi filter.

**Dampak kode/database:** Menata ulang template role form dan memindahkan script ke lokasi yang benar. Tidak ada perubahan backend, model, atau migration.

**Status pengujian:** Belum diverifikasi di browser server pengguna.

## 16. 2026-11-03 — Perbaikan AttributeError saat Tambah User

**Konteks/masalah:**
Saat Administrator menambah user dengan POST, `AdminUserForm.save()` memanggil `self.save_m2m()` setelah `super().save(commit=True)`. Pada alur ini Django `ModelForm` sudah menyimpan relasi many-to-many dan tidak menyediakan helper `save_m2m()` pada instance, sehingga muncul `AttributeError`.

**Keputusan/perbaikan:**
Hapus pemanggilan `self.save_m2m()` yang redundan. Pertahankan penyimpanan `UserProfile.toko` setelah user tersimpan. Perilaku password awal tetap unusable sampai Administrator menetapkan password.

**Dampak PRD:** Menambahkan kriteria penerimaan agar user, Group, dan pemetaan Toko tersimpan tanpa error.

**Dampak DDS/DDL:** Mendokumentasikan aturan `ModelForm.save(commit=True)` dan verifikasi untuk Admin Toko maupun role lain.

**Dampak kode/migration:** Mengubah `AdminUserForm.save()` pada `masterdata/admin_forms.py`. Tidak ada perubahan model atau migration.

**Status pengujian:** Perbaikan kode didasarkan pada perilaku Django `ModelForm`; belum diuji pada server pengguna. Setelah deployment, uji tambah user Admin Toko dengan Toko terpilih dan user role lain tanpa Toko.


## 17. 2026-11-03 — Arah Visual Frontend dan Penyegaran Dashboard

**Konteks/masalah:**
Audit Anti Slop mode AFTER menemukan arah visual belum terdokumentasi, lima tema belum memiliki token komponen yang cukup konsisten, dashboard masih memakai pola kartu statistik generik, serta shadow dan ikon digunakan secara berulang. Pemilik produk menyetujui temuan nomor 2, 3, 4, dan 5 untuk ditindaklanjuti.

**Pilihan yang dibahas:**
- Menetapkan identitas visual khusus tanpa mengubah aturan bisnis.
- Menata ulang dashboard agar berorientasi pada transaksi RO.
- Menyatukan lima tema melalui token semantik dan menyederhanakan elevasi/ikon.

**Keputusan yang disetujui:**
1. Karakter visual RO tenang, fungsional, profesional, dan berorientasi operasional.
2. Light menjadi tema default dengan dasar netral dan aksen biru; Dark, Ocean, Forest, dan Sunset tetap tersedia.
3. Kelima tema menggunakan token semantik bersama untuk background, surface, text, muted text, border, accent, focus, success, warning, dan danger.
4. Dashboard menonjolkan Daftar RO sebagai jalur kerja utama. Buat RO hanya ditampilkan untuk Administrator karena Admin Produksi tidak memiliki izin membuat transaksi RO pada endpoint saat ini.
5. Jumlah Dapur, Jadwal, Toko, dan Template Produk tetap menjadi informasi pendukung karena itulah data agregat yang disediakan view saat ini. Jangan menampilkan jumlah Draft/Terkirim sebelum query tersedia.
6. Permukaan komponen dibuat dominan datar; shadow dibatasi untuk overlay/elemen yang membutuhkan elevasi. Ikon hanya dipakai jika memperjelas fungsi atau entitas.
7. Tidak ada perubahan aturan bisnis, role, endpoint, model, atau migration dalam penyegaran ini.

**Alasan:**
Aplikasi adalah alat kerja operasional, sehingga hierarki informasi, keterbacaan, dan akses ke pekerjaan lebih penting daripada dekorasi. Token bersama membantu tema alternatif menjaga konsistensi. Dashboard harus menunjukkan tindakan yang benar-benar diizinkan oleh role dan tidak boleh menampilkan metrik yang belum didukung sumber data.

**Dampak PRD:**
Menambahkan standar visual frontend dan kriteria penerimaan untuk dokumentasi arah visual, tema, dashboard, penggunaan shadow/ikon, dan cakupan verifikasi.

**Dampak DDS/DDL/database:**
Menambahkan desain sistem tema berbasis token dan perilaku dashboard. Tidak ada perubahan schema atau migration.

**Dampak kode/migration:**
- Menambahkan `DESIGN.md`.
- Menata ulang `templates/masterdata/dashboard.html` menjadi jalur transaksi RO dan ringkasan master.
- Menyatukan token dan styling lima tema pada `static/css/themes.css`.
- Menyederhanakan override shell pada `static/css/sb-admin-overrides.css`.
- Membatasi tombol Buat RO pada dashboard untuk Administrator.
- Tidak ada perubahan model, endpoint, atau migration.

**Status implementasi dan pengujian:**
Perubahan source dan dokumentasi dikomit bertahap ke branch `main`. Belum dilakukan verifikasi browser/server, pengujian kontras, click-through, atau pengujian kelima tema pada desktop/tablet/mobile. Temuan 1 dan 6 dari audit tetap di luar cakupan perubahan ini.

**Referensi commit:**
Lihat riwayat commit branch `main` untuk `DESIGN.md`, template dashboard, CSS tema, dan dokumen ini.


## 15. 2026-11-04 — Penyelarasan frontend seluruh halaman CRUD

- **Konteks/masalah:** Setelah baseline desain frontend disetujui, halaman CRUD Master Data, User, dan Role masih memakai sejumlah gaya Bootstrap langsung, pola aksi yang padat, serta belum konsisten antar tema. Daftar User juga belum menyediakan pencarian.
- **Pilihan yang dibahas:** Memperbarui hanya tampilan; atau memperbarui tampilan sekaligus menambahkan pencarian daftar User.
- **Keputusan yang disetujui:** Pemilik produk menyetujui seluruh lingkup 1–7: (1) desain daftar master, (2) desain form tambah/ubah, (3) tombol aksi dan konfirmasi hapus, (4) penerapan token tema pada tabel/form/modal/validasi, (5) tampilan Manajemen User, (6) tampilan Manajemen Role dengan filter permission tetap dipertahankan, dan (7) pencarian User.
- **Alasan:** Menjaga konsistensi pengalaman CRUD dengan DESIGN.md dan mempercepat pencarian akun tanpa mengubah aturan bisnis.
- **Dampak PRD:** Tambahkan pencarian User pada kebutuhan Manajemen User dan kriteria penerimaan; penyegaran visual tidak mengubah kebutuhan bisnis yang ada.
- **Dampak DDS/DDL/database:** Pencarian menggunakan field User yang sudah tersedia; tidak memerlukan perubahan schema atau migration. Catat parameter pencarian dan pola antarmuka.
- **Dampak kode/migration:** Perubahan direncanakan pada template CRUD master dan admin, serta view User untuk pencarian. Tidak ada perubahan model/migration yang direncanakan.
- **Status implementasi dan pengujian:** Disetujui; implementasi dan pemeriksaan source akan dicatat setelah perubahan. Browser/runtime dan lima tema belum diverifikasi.
- **Referensi commit:** Diisi setelah implementasi.


### Status implementasi — 2026-11-04

- Penyegaran template daftar/form Master Data, daftar/form User, form password, daftar/form Role, dan halaman utama Administrasi telah diterapkan.
- Daftar User kini menerima parameter `q` dan memfilter username, first_name, last_name, serta email menggunakan pencocokan case-insensitive pada queryset Administrator.
- Filter permission Role tetap dipertahankan; elemen yang tidak cocok disembunyikan tanpa mengubah state checkbox.
- CSS CRUD menggunakan token tema yang sudah tersedia, termasuk `--bg-card`, `--bg-secondary`, `--text-primary`, `--text-secondary`, `--border-color`, `--accent-color`, dan warna status semantik.
- Tidak ada perubahan model, migration, aturan bisnis, endpoint, otorisasi, atau proses import/export.
- **Batas verifikasi:** perubahan telah diperiksa pada source code repository. Belum dilakukan browser rendering, click-through, pengujian lima tema/breakpoint, automated Django tests, Docker build, atau verifikasi runtime di server. Karena itu hasil belum boleh disebut lulus audit visual/runtime.
## 18. 2026-11-04 — Penambahan Operation Type Kirim dan Terima pada Master Dapur

**Konteks/masalah:** Master Dapur saat ini memiliki satu field `operation_type`. Kebutuhan operasional memerlukan pencatatan terpisah untuk operation type pengiriman dan penerimaan.

**Keputusan yang disetujui:**
1. Pertahankan field `operation_type` yang sudah ada.
2. Tambahkan `operation_type_kirim` dan `operation_type_terima` sebagai field teks bebas, masing-masing dengan batas panjang 120 karakter seperti field lama.
3. Tampilkan kedua field baru pada CRUD Master Dapur (daftar, tambah, ubah).
4. Sertakan kedua field pada pencarian daftar Dapur dan template impor/impor/ekspor Excel.
5. Tidak mengubah field `document`, master lain, atau alur transaksi RO.

**Dampak PRD:** Menambahkan kebutuhan tiga field operation type pada Master Dapur.

**Dampak DDS/DDL/database:** Menambahkan dua kolom CharField(120) pada tabel Dapur melalui migration baru. Record lama menerima string kosong pada saat migration; input baru wajib diisi melalui ModelForm.

**Dampak kode/migration:** Memperbarui model Dapur dan konfigurasi field CRUD; menambahkan migration `0007_dapur_operation_types.py`. ModelForm Dapur yang memakai `fields = "__all__"` menyajikan kedua field secara otomatis. Konfigurasi CRUD juga mengatur pencarian dan Excel.

**Status implementasi dan pengujian:** Source code dan dokumen diperbarui pada branch `main`. Belum dijalankan `makemigrations --check`, `migrate`, automated tests, Docker build, atau verifikasi browser/server. Migration perlu diuji pada salinan database sebelum deployment.

**Referensi commit:** Lihat riwayat branch `main` untuk perubahan model, CRUD, migration, dan dokumentasi.


## 19. 2026-11-04 — Adaptasi desain aplikasi ke SAP Fiori-inspired

**Konteks/masalah:** Pemilik produk memberikan file `sap_fiori_erp_dashboard_crud.html` dan meminta seluruh aplikasi RO menggunakan gaya visual yang semirip mungkin, mencakup font, ikon, tema, dashboard, dan komponen CRUD.

**Keputusan yang disetujui:** Gunakan file sebagai referensi desain utama. Adaptasi meliputi shell/header biru gelap, sidebar navigasi, font Inter, ikon Font Awesome, aksen biru Fiori, komponen CRUD, dan dashboard tile. Pertahankan tema yang sudah ada (Light, Dark, Ocean, Forest, Sunset), aturan bisnis, hak akses, endpoint, serta skema database.

**Batas adaptasi:** Tidak menyalin modul Material Management, KPI penjualan, stok, purchase order, chart, data contoh, atau fitur demo yang tidak ada di aplikasi RO. Dashboard hanya menampilkan hitungan master yang disediakan view dan pintasan transaksi yang sudah tersedia. Tidak menambahkan pencarian global/notifikasi semu yang tidak terhubung ke backend.

**Dampak PRD:** Menambahkan arah desain SAP Fiori-inspired dan batasan lingkup presentasi.

**Dampak DDS/DDL:** Mengubah template shell/dashboard dan CSS; tidak mengubah backend, model, migration, endpoint, atau proses.

**Status implementasi dan pengujian:** Source template, CSS, dan dokumen diperbarui pada branch main. Belum dilakukan browser rendering, click-through, pengujian lima tema, breakpoint, automated tests, Docker build, atau runtime server. Kesamaan visual hasil akhir belum tervalidasi.

**Referensi commit:** Lihat riwayat branch main untuk perubahan ini.

## 20. 2026-11-04 — Pengaturan Koneksi API Odoo (Tahap 1)

**Konteks/masalah:**
Aplikasi RO akan disiapkan untuk integrasi Odoo, tetapi pemilik produk membatasi tahap pertama pada pengaturan koneksi dan pengujian koneksi. Belum ada persetujuan untuk sinkronisasi atau pertukaran data RO.

**Keputusan:**
1. Tambahkan menu Administrator → Pengaturan API Odoo.
2. Simpan URL Odoo, database opsional, identitas user integrasi, dan API Key.
3. Simpan API Key dalam bentuk terenkripsi menggunakan Fernet dengan kunci khusus dari environment server `ODOO_API_ENCRYPTION_KEY`; jangan menyimpan kunci enkripsi pada Git.
4. Kolom API Key tidak pernah menampilkan nilai tersimpan. Saat edit, kolom kosong mempertahankan API Key sebelumnya.
5. Sediakan Test Connection terhadap endpoint Odoo 19 JSON-2 `POST /json/2/res.users/context_get`, menggunakan Bearer API Key dan header database bila diperlukan.
6. Wajib HTTPS untuk koneksi non-localhost. Simpan status, pesan, dan waktu pengujian.
7. Tahap ini tidak membaca, mengirim, atau menyinkronkan data RO.

**Alasan:**
JSON-2 adalah external API Odoo 19 yang menggunakan Bearer API Key. Endpoint `res.users/context_get` tanpa ID dapat mengidentifikasi context user dari API Key, sehingga cocok untuk uji autentikasi read-only. Kunci enkripsi terpisah mencegah ketergantungan langsung pada rotasi Django SECRET_KEY.

**Dampak PRD:** Menambahkan kebutuhan, batasan keamanan, dan kriteria penerimaan pengaturan koneksi tahap pertama.

**Dampak DDS/DDL/database:** Menambahkan model singleton `OdooConnectionSetting`, migration `0008_odooconnectionsetting.py`, endpoint Administrator, protokol JSON-2, dan konfigurasi environment.

**Dampak kode:** Menambahkan dependensi `requests` dan `cryptography`, halaman `templates/admin_tools/odoo_connection.html`, menu dashboard Administrator, serta view pengaturan dan Test Connection.

**Status implementasi dan pengujian:** Source dan dokumentasi diperbarui pada branch `main`. Belum diuji dengan instance Odoo pengguna, belum dilakukan Docker build, penerapan migration, atau verifikasi browser/server. Jangan menyatakan koneksi berhasil sebelum Test Connection dijalankan pada lingkungan pengguna.

**Catatan operasional:** Pemilik server harus membuat dan menyimpan `ODOO_API_ENCRYPTION_KEY` secara aman pada file `.env` server sebelum menggunakan halaman ini. Kunci harus dicadangkan; jika hilang, API Key tersimpan harus dimasukkan ulang.

**Referensi teknis:** Dokumentasi resmi Odoo 19 External JSON-2 API: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html

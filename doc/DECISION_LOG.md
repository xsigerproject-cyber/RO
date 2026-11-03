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

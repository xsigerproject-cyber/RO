# DESIGN — Arah Visual Aplikasi RO

## Tujuan
Antarmuka RO adalah alat kerja operasional internal untuk input dan peninjauan Requisition Order (RO), pengelolaan master, dan administrasi. Desain harus membantu pengguna menyelesaikan pekerjaan dengan cepat, membaca data dengan teliti, dan memahami status tanpa ornamen yang tidak perlu.

## Prinsip
1. **Clarity over decoration:** label, nilai, status, validasi, dan tindakan harus lebih menonjol daripada dekorasi.
2. **Task-oriented:** halaman disusun mengikuti pekerjaan dan keputusan pengguna, bukan sekadar mengisi ruang dengan kartu.
3. **Consistent and predictable:** pola tombol, form, tabel, navigasi, empty state, dan feedback konsisten.
4. **Responsive by default:** tabel boleh memakai overflow horizontal yang terkontrol; kontrol dan teks tidak boleh saling menimpa pada layar sempit.
5. **Accessible:** warna bukan satu-satunya pembawa makna; gunakan label teks, fokus keyboard yang jelas, kontras yang memadai, dan target interaksi yang nyaman.
6. **Honest data:** angka dashboard berasal dari query aplikasi yang tersedia. Jangan menampilkan metrik, status, atau grafik yang belum didukung data.

## Karakter visual
- Karakter: tenang, fungsional, profesional, dan berorientasi operasional.
- Kepadatan: informasi cukup padat untuk pekerjaan back-office, tetapi diberi jarak antar kelompok informasi.
- Tipografi: system sans-serif untuk keterbacaan dan performa; hierarki jelas antara judul halaman, subjudul, label, nilai, dan bantuan.
- Layout: latar netral, konten terstruktur, garis pemisah halus, dan permukaan datar.
- Ikon: gunakan hanya saat mempercepat pengenalan fungsi/entitas; jangan menduplikasi teks label.
- Elevasi: default tanpa shadow. Elevasi hanya untuk overlay atau elemen yang benar-benar harus terangkat dari konten.

## Warna dan tema
Light adalah tema default dan acuan utama:
- Latar halaman: netral terang.
- Permukaan: putih.
- Teks utama: abu-abu sangat gelap.
- Teks sekunder: abu-abu dengan kontras terbaca.
- Aksen utama: biru untuk aksi primer dan fokus.
- Status sukses, peringatan, dan bahaya memakai warna semantik serta label teks.

Tema alternatif yang tetap didukung:
- **Dark:** permukaan gelap dengan teks terang dan aksen biru yang tetap terbaca.
- **Ocean:** latar biru pucat, permukaan putih, aksen biru laut.
- **Forest:** latar hijau pucat, permukaan putih, aksen hijau hutan.
- **Sunset:** latar hangat pucat, permukaan putih, aksen terracotta.

Semua tema harus menggunakan token semantik yang sama (background, surface, text, muted text, border, accent, focus, success, warning, danger). Komponen tidak boleh mengandalkan warna hard-coded tema Light jika token tersedia. Tema harus mempertahankan makna status dan hierarki kontrol yang sama.

## Pola komponen
- **Page heading:** judul ringkas dan deskripsi kontekstual; hindari badge dekoratif yang mengulang judul.
- **Primary action:** satu tindakan utama yang paling relevan untuk halaman; tindakan sekunder tampil lebih tenang.
- **Forms:** label eksplisit, bantuan dekat field, error dekat field, dan grouping berdasarkan tugas.
- **Tables:** judul kolom jelas, alignment konsisten, status berlabel, aksi record terpisah dari data utama.
- **Cards/panels:** gunakan hanya untuk mengelompokkan konten yang memang memiliki batas konseptual. Utamakan border halus daripada shadow.
- **Feedback:** gunakan alert/toast untuk hasil aksi dan empty state yang menjelaskan langkah berikutnya.
- **Dashboard:** utamakan pintasan kerja RO dan akses master yang relevan. Statistik hanya ditampilkan bila datanya tersedia dan membantu keputusan.

## Dashboard saat ini
Dashboard memakai konteks jumlah Dapur, Jadwal, Toko, dan Template Produk dari view yang ada. Dashboard tidak boleh mengklaim jumlah Draft/Terkirim atau ringkasan produksi sebelum view menyediakan query yang benar. Tampilkan Buat RO dan Daftar RO sebagai jalur kerja utama, lalu jumlah master sebagai informasi pendukung.

## Batasan
- Tidak mengubah aturan bisnis, role, alur RO, skema database, atau kontrak endpoint sebagai bagian dari penyegaran visual.
- Jangan menambahkan chart, metrik, atau fitur yang tidak memiliki sumber data.
- Jangan menghapus tema alternatif tanpa keputusan terpisah.
- Setiap perubahan UI perlu diverifikasi pada lima tema dan breakpoint desktop, tablet, serta mobile sebelum dinyatakan selesai.

## Status
Baseline arah visual disetujui pemilik produk pada 3 November 2026. Dokumen ini menjadi rujukan untuk pekerjaan frontend berikutnya; perubahan arah visual perlu dicatat pada Decision Log.

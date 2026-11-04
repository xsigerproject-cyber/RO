# Audit dan Operasional Koneksi API Odoo 19

## Cakupan

Tahap 1 hanya mengelola konfigurasi koneksi dan menguji autentikasi. Tidak ada sinkronisasi, pembacaan, atau penulisan data RO.

## Konfigurasi rahasia

Aplikasi membaca `ODOO_API_ENCRYPTION_KEY` dari environment server. Buat key Fernet baru:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Masukkan hasilnya ke `.env` sebagai `ODOO_API_ENCRYPTION_KEY=<hasil>`. Jangan commit key asli ke Git. Cadangkan key secara terpisah dan aman dari backup database. Kehilangan key membuat API key tersimpan tidak dapat didekripsi; key baru tidak dapat membuka ciphertext lama.

## Field konfigurasi

- **URL Odoo**: URL dasar instance tanpa path, query, fragment, atau kredensial. HTTPS diwajibkan untuk host selain localhost.
- **Database**: opsional; dikirim sebagai header `X-Odoo-Database` jika diisi.
- **User Integrasi**: label/referensi operator untuk dokumentasi konfigurasi. Identitas autentikasi aktual ditentukan oleh pemilik API Key Odoo, bukan oleh nilai field ini.
- **API Key**: dienkripsi menggunakan Fernet. Kolom kosong saat edit mempertahankan key sebelumnya.

## Alur Test Connection

1. Simpan konfigurasi yang sudah divalidasi.
2. Dekripsi API Key di server.
3. Kirim `POST /json/2/res.users/context_get` dengan Bearer API Key, `Content-Type: application/json`, body JSON kosong, dan header database opsional.
4. Redirect tidak diikuti.
5. HTTP 200 baru dinyatakan berhasil jika body dapat dibaca sebagai objek JSON.
6. HTTP 401/403 ditampilkan sebagai kegagalan autentikasi; 404 sebagai endpoint tidak ditemukan; error jaringan, timeout, respons tidak valid, dan status lain dicatat sebagai gagal.

Endpoint ini hanya menguji apakah API Key dapat memanggil method context user. Keberhasilan tidak membuktikan hak akses untuk model atau operasi sinkronisasi RO di masa depan.

## Pemeriksaan keamanan

- Halaman dan POST dibatasi untuk Administrator/superuser melalui decorator aplikasi.
- Form memakai CSRF token.
- API Key tersimpan terenkripsi dan tidak pernah diisi ulang ke form.
- Jangan menaruh API Key atau encryption key pada URL, log, dokumentasi, screenshot, atau commit.
- Batasi akses server dan backup karena database menyimpan ciphertext serta metadata koneksi.

## Checklist verifikasi runtime

Pengujian berikut masih harus dilakukan pada lingkungan deployment yang memiliki database dan instance Odoo nyata:

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate --plan`
- Login sebagai Administrator: halaman dapat dibuka dan konfigurasi dapat disimpan.
- Login sebagai non-Administrator: akses ditolak.
- Simpan pertama tanpa API Key: form menolak.
- Simpan konfigurasi dengan API Key: database hanya berisi ciphertext, bukan plaintext.
- Edit dengan kolom API Key kosong: ciphertext lama tetap sama.
- Test dengan key valid: status berhasil.
- Test dengan key salah, endpoint salah, timeout, redirect, dan respons non-JSON: status gagal dengan pesan aman.
- Uji startup Docker setelah environment key tersedia.

Belum ada klaim bahwa pemeriksaan runtime atau koneksi ke instance Odoo pengguna telah lulus.

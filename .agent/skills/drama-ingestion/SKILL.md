---
name: drama-ingestion
description: Standard Operating Procedure (SOP) and rules for ingesting short dramas from Vidrama, uploading to Cloudflare R2, and registering in KingShort DB.
---

# SOP & Aturan Sedot Drama KingShort (Drama Ingestion Skill)

Panduan operasional standar ini wajib diikuti oleh AI saat melakukan *ingestion* (sedot drama) dari Vidrama ke Cloudflare R2 dan Database KingShort.

---

## 1. Penanganan Cover Drama (KRUSIAL - Pencegahan Error HEIC & CDN Cache)

### A. Konversi Wajib ke JPEG Murni
* Gambar cover yang didapat dari Vidrama sering kali berformat **HEIC** (Apple HEVC Image) atau WebP di balik URL/nama file `.jpg` atau `.heic`.
* **DILARANG** langsung menyimpan/mengunggah byte mentah cover dari Vidrama ke R2.
* **WAJIB** mengonversinya terlebih dahulu menggunakan FFmpeg agar menjadi file Standard Progressive JPEG murni:
  ```bash
  ffmpeg -y -i cover_raw -update 1 -q:v 2 cover_clean.jpg
  ```
* Pastikan `Content-Type: image/jpeg` saat diunggah ke Cloudflare R2.

### B. Menghindari Cache Cloudflare Edge CDN
* Bucket R2 terhubung dengan CDN Cloudflare yang memiliki kebijakan *cache-control* 1 tahun (`max-age=31536000`).
* Jika memperbaiki atau memperbarui cover pada drama yang sudah ada, **WAJIB menggunakan nama file baru di R2** (misalnya `cover_hq.jpg` atau `cover_v2.jpg`).
* **JANGAN** menggunakan nama file lama yang ditimpa, karena Cloudflare Edge akan tetap menyajikan file lama dari *cache*.

### C. URL Cover Bersih untuk Next.js Image Optimization
* Simpan URL cover di database KingShort **tanpa query parameter (`?v=...`)** (contoh: `https://stream.shortlovers.id/melolo/slug-drama/cover_hq.jpg`).
* Parameter query dapat menyebabkan komponen *Next.js Image Optimization* di halaman detail Admin Panel gagal melakukan *fetching/resizing*.

---

## 2. Pendaftaran Drama & Episode di KingShort DB

### A. Pembuatan Drama (`POST /api/admin/dramas`)
* Header wajib: `x-admin-key: 00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14`
* Payload utama menggunakan properti:
  * `cover`: URL cover JPEG murni (bukan `coverUrl`)
  * `genres`: Array genre (bukan `categories`)
  * `status`: `'completed'` atau `'ongoing'`

### B. Aktivasi Drama & Episode
* Drama baru yang dibuat via API secara default berstatus nonaktif (`isActive: False`).
* **WAJIB** mengaktifkan drama setelah selesai diproses dengan `PATCH /api/admin/dramas/{id}` payload `{'isActive': True}`.
* Setiap episode yang didaftarkan juga **WAJIB** berstatus `isActive: True`.

---

## 3. Pengaturan Fitur VIP / Gratis (Non-VIP)

* Jika pengguna meminta menonaktifkan fitur VIP pada drama (semua episode gratis):
  * Gunakan endpoint `PATCH /api/episodes/{ep_id}` untuk setiap episode dengan payload:
    ```json
    {
      "isVip": false,
      "coinPrice": 0,
      "isActive": true
    }
    ```

---

## 4. API Endpoints Vidrama

### Provider `melolov3` / `melolo`:
* Detail Drama & Daftar Episode:
  ```
  GET https://vidrama.asia/api/melolov3/series?id=<VIDRAMA_ID>&lang=id
  ```
* Daftar URL Video Stream Langsung (MP4):
  ```
  GET https://vidrama.asia/api/melolov3/multi-video?id=<VIDRAMA_ID>&lang=id
  ```

### Provider `dramawavev2`:
* Detail Drama:
  ```
  GET https://vidrama.asia/api/dramawavev2?action=detail&id=<VIDRAMA_ID>&lang=in
  ```
* Stream Episode:
  ```
  GET https://vidrama.asia/api/dramawavev2?action=stream&id=<VIDRAMA_ID>&chapterId=<CHAPTER_ID>&episode=<EP_NO>
  ```

---

## 5. Mode Penyimpanan

* **Mode R2 Saja (Khusus Cloud)**: Jika pengguna meminta "simpan di R2 saja, jangan di folder lokal", unduh stream ke direktori *temporary*, konversi 720p & 540p, unggah ke R2, lalu langsung hapus file *temporary*.
* **Mode Burning Lokal**: Jika pengguna meminta pembakaran subtitle (*hardsub*) ke folder lokal, gunakan ukuran font subtitle sesuai permintaan (misalnya Font Size 13) dan simpan di folder `D:/Video Drama/Facebook/<Judul Drama>/`.

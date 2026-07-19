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

## 5. Subtitle Detection & Handling (WAJIB — Berlaku Semua Provider)

> 🔴 **MANDATORY:** Setiap kali menyedot drama baru, WAJIB cek status subtitle terlebih dahulu sebelum melanjutkan ingestion.

### A. Deteksi Burned-in vs Soft Subtitle

1. **Probe video source** menggunakan `ffprobe` untuk menghitung jumlah stream:
   ```bash
   ffprobe -v quiet -print_format json -show_streams <SOURCE_URL>
   ```
2. **Jika hanya 2 stream** (1 video + 1 audio) → subtitle kemungkinan **burned-in**.
3. **Konfirmasi visual**: Screenshot 1 frame dan lihat apakah ada teks di gambar:
   ```bash
   ffmpeg -y -ss 15 -i <SOURCE_URL> -frames:v 1 -update 1 /tmp/check_frame.jpg
   ```

### B. Jika Subtitle BURNED-IN (Hardcoded ke Pixel Video)
* ✅ Tidak perlu berbuat apa-apa — subtitle sudah ada di video.
* ✅ Tidak perlu upload VTT atau daftarkan ke tabel `subtitles`.
* Provider yang biasanya burned-in: **melolov3**, **melolo**.

### C. Jika Subtitle BELUM Burned-in (Soft / External)
* **WAJIB** cari URL VTT/SRT dari response API provider (cek field `subtitles`, `tracks`, dll).
* **WAJIB** download file VTT tersebut.
* **WAJIB** upload ke R2 di path: `dramas/netshort/{slug}/ep{NNN}_id.vtt`
* **WAJIB** daftarkan ke tabel `subtitles` via API:
  ```json
  POST /api/episodes/{ep_id}/subtitles
  {
    "language": "id",
    "label": "Indonesian",
    "url": "https://stream.shortlovers.id/dramas/netshort/{slug}/ep001_id.vtt",
    "isDefault": true
  }
  ```
* Provider yang biasanya soft subtitle: **dramawavev2**.

---

## 6. Video Encoding Requirements (WAJIB)

> 🔴 **MANDATORY:** Semua video yang diupload ke R2 HARUS menggunakan `-movflags +faststart`.

### Kenapa Faststart Wajib?
* `+faststart` memindahkan metadata MP4 (moov atom) ke awal file.
* Tanpa ini, browser/player harus menunggu seluruh file ter-download sebelum bisa memutar video.
* Dengan faststart, video bisa langsung diputar sambil streaming (progressive playback).

### FFmpeg Command Standar (720p):
```bash
ffmpeg -y -i input.mp4 \
  -vf scale=720:-2 \
  -c:v libx264 -crf 23 -preset fast \
  -maxrate 1500k -bufsize 3000k \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  output_720p.mp4
```

### FFmpeg Command Standar (540p):
```bash
ffmpeg -y -i input_720p.mp4 \
  -vf scale=540:-2 \
  -c:v libx264 -crf 26 -preset fast \
  -maxrate 1000k -bufsize 2000k \
  -c:a aac -b:a 96k \
  -movflags +faststart \
  output_540p.mp4
```

---

## 7. Mode Penyimpanan

* **Mode R2 Saja (Khusus Cloud)**: Jika pengguna meminta "simpan di R2 saja, jangan di folder lokal", unduh stream ke direktori *temporary*, konversi 720p & 540p dengan faststart, unggah ke R2, lalu langsung hapus file *temporary*.
* **Mode Burning Lokal**: Jika pengguna meminta pembakaran subtitle (*hardsub*) ke folder lokal, gunakan ukuran font subtitle sesuai permintaan (misalnya Font Size 13) dan simpan di folder `D:/Video Drama/Facebook/<Judul Drama>/`.

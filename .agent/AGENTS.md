# Workspace Rules & Skills KingShort (`kingshortid`)

## 1. Skill Wajib untuk Sedot Drama (`drama-ingestion`)
Setiap kali diminta untuk menyedot/mengunduh drama baru atau memperbaiki drama yang ada di KingShort:
* **WAJIB** membaca dan menerapkan instruksi dari skill `@[skills/drama-ingestion]` (`d:\kingshortid\.agent\skills\drama-ingestion\SKILL.md`).

Aturan utama dalam `drama-ingestion`:
1. **Konversi Cover ke JPEG Murni**: Gunakan `ffmpeg -update 1` untuk mengubah file asal (HEIC/WebP) menjadi JPEG murni sebelum diunggah ke R2.
2. **Hindari Cache CDN Cloudflare**: Jika menimpa/memperbaiki cover, gunakan nama file baru (misal `cover_hq.jpg`) agar tidak terkena cache CDN 1 tahun.
3. **URL Bersih untuk Next.js Image Optimization**: Simpan URL cover di database tanpa parameter query (`?v=...`).
4. **Pendaftaran DB KingShort**: Gunakan properti `cover` dan `genres` pada payload POST drama, serta pastikan `isActive: True` pada drama dan semua episodenya.

## 2. Aturan Subtitle (WAJIB — Berlaku Semua Drama)
Setiap kali menyedot drama baru (provider apapun), WAJIB lakukan cek berikut **SEBELUM** memulai ingestion:

1. **Deteksi burned-in**: Probe source video dengan `ffprobe -show_streams` → hitung jumlah stream.
   - 2 stream (video+audio) = kemungkinan burned-in → konfirmasi dengan screenshot frame:
     ```bash
     ffmpeg -y -ss 15 -i <SOURCE_URL> -frames:v 1 -update 1 /tmp/check_frame.jpg
     ```
   - 3+ stream atau ada `codec_type=subtitle` = soft subtitle.

2. **Jika BURNED-IN**: Tidak perlu lakukan apapun — subtitle sudah ada di pixel video.
   - Provider yang *biasanya* burned-in: `melolov3`, `melolo`.

3. **Jika SOFT SUBTITLE (belum burned-in)**:
   - WAJIB cari URL VTT dari response API provider (field: `subtitles`, `tracks`, dll).
   - WAJIB download file VTT ke temp dir.
   - WAJIB upload ke R2: `dramas/netshort/{slug}/ep{NNN}_id.vtt`
   - WAJIB daftarkan ke DB via `POST /api/episodes/{ep_id}/subtitles`:
     ```json
     { "language": "id", "label": "Indonesian", "url": "...", "isDefault": true }
     ```
   - Provider yang *biasanya* soft subtitle: `dramawavev2`.

## 3. Aturan Video Encoding (WAJIB)
Semua video yang diupload ke R2 HARUS memenuhi syarat berikut:

* **`-movflags +faststart`** WAJIB ada di setiap ffmpeg command — memindahkan moov atom ke awal file agar video bisa diplay langsung saat streaming tanpa download penuh dulu.
* Resolusi standar: **720p** (primary) + **540p** (fallback).
* Codec: `libx264` (video), `aac` (audio).

Command standar 720p:
```bash
ffmpeg -y -i input.mp4 -vf scale=720:-2 -c:v libx264 -crf 23 -preset fast \
  -maxrate 1500k -bufsize 3000k -c:a aac -b:a 128k -movflags +faststart output_720p.mp4
```
Command standar 540p:
```bash
ffmpeg -y -i input_720p.mp4 -vf scale=540:-2 -c:v libx264 -crf 26 -preset fast \
  -maxrate 1000k -bufsize 2000k -c:a aac -b:a 96k -movflags +faststart output_540p.mp4
```

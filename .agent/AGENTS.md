# Workspace Rules & Skills KingShort (`kingshortid`)

## 1. Skill Wajib untuk Sedot Drama (`drama-ingestion`)
Setiap kali diminta untuk menyedot/mengunduh drama baru atau memperbaiki drama yang ada di KingShort:
* **WAJIB** membaca dan menerapkan instruksi dari skill `@[skills/drama-ingestion]` (`d:\kingshortid\.agent\skills\drama-ingestion\SKILL.md`).

Aturan utama dalam `drama-ingestion`:
1. **Konversi Cover ke JPEG Murni**: Gunakan `ffmpeg -update 1` untuk mengubah file asal (HEIC/WebP) menjadi JPEG murni sebelum diunggah ke R2.
2. **Hindari Cache CDN Cloudflare**: Jika menimpa/memperbaiki cover, gunakan nama file baru (misal `cover_hq.jpg`) agar tidak terkena cache CDN 1 tahun.
3. **URL Bersih untuk Next.js Image Optimization**: Simpan URL cover di database tanpa parameter query (`?v=...`).
4. **Pendaftaran DB KingShort**: Gunakan properti `cover` dan `genres` pada payload POST drama, serta pastikan `isActive: True` pada drama dan semua episodenya.

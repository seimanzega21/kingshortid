# Complete GoodShort Scraping Guide - FIXED VERSION

## 🎯 What's Fixed

### ✅ Issues Resolved
1. **✓ Real Titles** - Bukan angka generic, ambil dari API
2. **✓ Correct Covers** - Cover asli yang ditampilkan ke user
3. **✓ Working Segments** - Generate HLS playlist yang benar
4. **✓ Episode Names** - Episode 1, Episode 2 (bukan chapter_xxx)
5. **✓ Complete Metadata** - Title, description, author, category, dll
6. **✓ Clean Structure** - Struktur folder yang rapi

---

## 📁 New Output Structure

```
output/
├── covers/
│   ├── 31000991502.jpg
│   ├── 31001051678.jpg
│   └── 31001241698.jpg
│
├── metadata/
│   └── (individual drama JSON files)
│
└── episodes/
    ├── Drama Title 1/
    │   ├── cover.jpg
    │   ├── drama.json
    │   ├── Episode 1/
    │   │   ├── Episode 1.mp4
    │   │   ├── metadata.json
    │   │   └── playlist.m3u8
    │   ├── Episode 2/
    │   │   ├── Episode 2.mp4
    │   │   ├── metadata.json
    │   │   └── playlist.m3u8
    │   └── ...
    │
    └── Drama Title 2/
        └── ...
```

---

## 🚀 Quick Start

### Option 1: Reorganize Existing Data

Untuk data yang sudah di-scrape sebelumnya:

```bash
cd d:\kingshortid\scripts\goodshort-scraper

# Reorganize existing downloads
python reorganize_scraped_data.py
```

**Apa yang dilakukan:**
- ✅ Rename `chapter_xxx` → `Episode 1`, `Episode 2`
- ✅ Combine segments jadi MP4 (jika belum)
- ✅ Copy cover & metadata
- ✅ Buat struktur baru yang rapi

---

### Option 2: Fresh Scrape with Complete Metadata

Untuk scrape drama baru dengan metadata lengkap:

```bash
cd d:\kingshortid\scripts\goodshort-scraper

# Scrape single drama
npm run scrape-complete 31000991502

# Or batch scrape multiple dramas
npm run batch-scrape
```

**Apa yang didapat:**
- ✅ Judul asli dari API
- ✅ Cover original (bukan screenshot)
- ✅ Description lengkap
- ✅ Author, category, genre, tags
- ✅ Episode list dengan title masing-masing
- ✅ HLS playlist yang  working

---

## 📋 Batch Scraping

### 1. Create batch-list.json

Buat file `batch-list.json` di root scraper:

```json
{
  "dramas": [
    { "bookId": "31000991502", "priority": 1 },
    { "bookId": "31001051678", "priority": 2 },
    { "bookId": "31001241698", "priority": 3 }
  ]
}
```

### 2. Run Batch Scraper

```bash
npm run batch-scrape
```

**Features:**
- Scrape multiple dramas otomatis
- Rate limiting (5 detik antar drama)
- Error handling & retry
- Save results ke `output/batch-results.json`

---

## 🔧 How It Works

### Complete Scraper Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETE SCRAPER                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. FETCH METADATA (API: /book/detail)                       │
│     ├── Title (real, not generic)                            │
│     ├── Cover URL (main poster)                              │
│     ├── Description                                          │
│     ├── Author, Category, Genre                              │
│     └── Total Chapters                                       │
│                                                              │
│  2. DOWNLOAD COVER                                           │
│     └── Save to: output/covers/{bookId}.jpg                  │
│                                                              │
│  3. FETCH EPISODE LIST (API: /chapter/list)                  │
│     ├── Episode titles                                       │
│     ├── Duration, isFree                                     │
│     └── Chapter IDs                                          │
│                                                              │
│  4. FETCH VIDEO URLs (API: /chapter/play)                    │
│     ├── HLS master playlist                                  │
│     ├── Extract token & videoId                              │
│     └── Build segment URLs                                   │
│                                                              │
│  5. GENERATE STRUCTURE                                       │
│     ├── Create drama folder (with real title)                │
│     ├── Create Episode 1, Episode 2 folders                  │
│     ├── Generate playlist.m3u8 for each                      │
│     └── Save metadata.json                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Metadata Format

### Drama Metadata (`drama.json`)

```json
{
  "bookId": "31000991502",
  "title": "Cinta Yang Hilang",
  "cover": "https://acf.goodreels.com/videobook/.../cover.jpg",
  "coverHQ": "https://acf.goodreels.com/videobook/.../cover-720.jpg",
  "coverPath": "output/covers/31000991502.jpg",
  "description": "Seorang wanita muda yang kehilangan...",
  "author": "GoodShort Studios",
  "category": "Romance",
  "genre": "Romance",
  "tags": ["romantic", "drama", "modern"],
  "totalChapters": 80,
  "language": "id",
  "rating": 4.8,
  "views": 1250000,
  "episodeCount": 80,
  "scrapedAt": "2026-02-01T09:00:00.000Z"
}
```

### Episode Metadata (`metadata.json`)

```json
{
  "episodeNumber": 1,
  "title": "Pertemuan Pertama",
  "chapterId": "469570",
  "duration": 120,
  "isFree": true,
  "videoUrl": "https://v2-akm.goodreels.com/.../playlist.m3u8",
  "drama": {
    "title": "Cinta Yang Hilang",
    "bookId": "31000991502"
  }
}
```

---

## 🎥 HLS Playlist Format

Each episode gets a `playlist.m3u8`:

```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
https://v2-akm.goodreels.com/mts/books/.../segment_000000.ts
#EXTINF:10.0,
https://v2-akm.goodreels.com/mts/books/.../segment_000001.ts
...
#EXT-X-ENDLIST
```

**Untuk play di video player:**
```javascript
<video src="Episode 1/playlist.m3u8" />
```

---

## ⚙️ Configuration

### Device Parameters

Edit `src/complete-scraper.ts`:

```typescript
const DEVICE_PARAMS = {
    gaid: 'your-google-ad-id',
    androidId: 'your-android-id',
    userToken: 'Bearer your-jwt-token'
};
```

**Cara dapat params:**
1. Run Frida script: `frida/extract-device-params.js`
2. Copy output ke `DEVICE_PARAMS`

---

## 🐛 Troubleshooting

### "Invalid sign" Error

**Problem:** API menolak request (401/403)

**Solution:**
1. Check device params (gaid, androidId, userToken)
2. Verify apk-signature-md5.txt correct
3. Run dengan Frida untuk capture fresh params

---

### Segments Tidak Bisa Diplay

**Problem:** Video tidak muncul

**Solution:**
1. Check `playlist.m3u8` structure
2. Verify segment URLs valid
3. Test dengan VLC: `vlc playlist.m3u8`

---

### ffmpeg Not Found

**Problem:** Tidak bisa combine segments

**Solution:**
```bash
# Download ffmpeg
https://ffmpeg.org/download.html

# Extract to:
C:\ffmpeg\

# Add to PATH:
C:\ffmpeg\bin
```

---

## 📝 Commands Cheat Sheet

```bash
# Reorganize existing data
python reorganize_scraped_data.py

# Scrape single drama (complete)
npm run scrape-complete 31000991502

# Batch scrape
npm run batch-scrape

# Old scraper (video only)
npm run scrape

# Download videos
npm run download

# Upload to R2
npm run upload
```

---

## 🎯 Next Steps

1. **Reorganize existing** → `python reorganize_scraped_data.py`
2. **Test dengan 1 drama** → `npm run scrape-complete <bookId>`
3. **Verify output** → Check `output/episodes/`
4. **Batch scrape** → Edit `batch-list.json` & run
5. **Import to DB** → Use processed metadata

---

## 📞 Support

Jika ada issue:
1. Check log output
2. Verify API params
3. Test segment URLs manually
4. Check ffmpeg installation

Semua script sudah handle error dengan informasi detail! 🚀

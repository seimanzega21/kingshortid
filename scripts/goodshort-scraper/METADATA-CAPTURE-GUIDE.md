# Complete Metadata Capture Guide

## Overview
Panduan untuk capture metadata lengkap (cover, judul, deskripsi, genre, author) dari GoodShort.

## Quick Start

### Prerequisites
1. Emulator Android (LDPlayer/NoxPlayer/BlueStacks) berjalan
2. GoodReels app terinstall di emulator
3. Frida terinstall: `pip install frida-tools`
4. USB Debugging enabled

### Step 1: Run Capture Script
```cmd
cd d:\kingshortid\scripts\goodshort-scraper
start-capture-enhanced.bat
```

Atau manual:
```cmd
frida -U -f com.newreading.goodreels -l frida\capture-metadata-enhanced.js --no-pause
```

### Step 2: Browse Dramas
Di app GoodReels:
1. Buka tab **Indonesian/Drama Indonesia**
2. **Scroll** untuk capture list dramas (bulk metadata)
3. **Tap** pada drama untuk capture metadata detail
4. **Putar video** untuk capture episode URLs

### Step 3: Monitor Progress
Di console Frida, ketik:
- `status()` - Lihat statistik capture
- `list()` - Lihat daftar drama yang sudah dicapture

### Step 4: Export Data
Ketik `save()` di console Frida. Copy output JSON.

Save ke file:
```
d:\kingshortid\scripts\goodshort-scraper\scraped_data\metadata_complete.json
```

### Step 5: Process Data
```cmd
python process_captured_metadata.py
```

Script akan:
- Parse metadata dari JSON
- Download cover images
- Update `books_metadata.json`
- Simpan individual drama files ke `scraped_data/metadata/`

---

## Data yang Dicapture

### Per Drama
| Field | Source |
|-------|--------|
| `title` | API /book response |
| `description` | API /book response |
| `cover` | CDN + API response |
| `author` | API /book response |
| `category/genre` | API /book response |
| `totalChapters` | API /book response |
| `chapterList` | API /chapter response |

### Per Episode
| Field | Source |
|-------|--------|
| `chapterId` | Video CDN URL |
| `token` | Video CDN URL |
| `videoId` | Video CDN URL |
| `title` | API /chapter response |
| `isFree` | API /chapter response |

---

## Workflow Lengkap

```
┌─────────────────────────────────────────────────────────────────┐
│                    METADATA CAPTURE WORKFLOW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. START CAPTURE                                               │
│     └── start-capture-enhanced.bat                              │
│                                                                 │
│  2. BROWSE APP (GoodReels)                                      │
│     ├── Scroll drama list → Bulk metadata                       │
│     ├── Tap drama details → Full metadata                       │
│     └── Watch episodes → Video URLs                             │
│                                                                 │
│  3. EXPORT (Frida console)                                      │
│     └── save() → Copy JSON                                      │
│                                                                 │
│  4. SAVE JSON                                                   │
│     └── scraped_data/metadata_complete.json                     │
│                                                                 │
│  5. PROCESS                                                     │
│     └── python process_captured_metadata.py                     │
│         ├── Download covers                                     │
│         ├── Update books_metadata.json                          │
│         └── Save individual drama files                         │
│                                                                 │
│  6. VERIFY                                                      │
│     └── Check scraped_data/books_metadata.json                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `frida/capture-metadata-enhanced.js` | Main capture script |
| `start-capture-enhanced.bat` | Easy launcher |
| `process_captured_metadata.py` | Post-processor |
| `scraped_data/metadata_complete.json` | Raw capture output |
| `scraped_data/books_metadata.json` | Processed metadata |
| `scraped_data/covers/` | Downloaded cover images |
| `scraped_data/metadata/` | Individual drama JSON |

---

## Troubleshooting

### "Frida not found"
```cmd
pip install frida-tools
```

### "Unable to find device"
1. Pastikan emulator berjalan
2. Coba: `adb devices` untuk verify
3. Restart adb: `adb kill-server && adb start-server`

### "Process not found"
App belum running. Script akan spawn otomatis dengan `-f` flag.

### Metadata tidak tercapture
- Pastikan membuka **drama detail page** (bukan hanya scroll)
- Tunggu halaman load sepenuhnya
- Check console untuk error messages

---

## Expected Output

After processing, `books_metadata.json` should look like:
```json
{
  "31000991502": {
    "bookId": "31000991502",
    "title": "Cinta Tersembunyi",
    "cover": "https://acf.goodreels.com/videobook/.../cover-720.jpg",
    "coverLocal": "scraped_data/covers/31000991502_cover.jpg",
    "description": "Drama romantis tentang...",
    "author": "GoodShort Studio",
    "category": "Romance",
    "genre": "Romance",
    "totalChapters": 80,
    "episodesCaptured": 80,
    "language": "id",
    "source": "goodshort",
    "needsUpdate": false
  }
}
```

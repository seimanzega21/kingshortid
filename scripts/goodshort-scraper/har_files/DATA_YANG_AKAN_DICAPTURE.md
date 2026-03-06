# Data yang Akan Di-Capture dari HAR

## ✅ COMPLETE DATA CHECKLIST

### 1. **Book/Drama Metadata** (dari `/book/quick/open`)

**Akan di-extract:**
- ✅ `bookId` - ID unik drama
- ✅ `bookName` - Judul drama (contoh: "Cinta di Waktu yang Tepat")
- ✅ `description` - Synopsis/deskripsi cerita
- ✅ `chapterCount` - Total episode (biasanya 70-100)
- ✅ `coverUrl` - URL gambar cover/poster
- ✅ `tags` - Category/genre
- ✅ `score` - Rating

**Endpoint**: `https://api.myshort.click/hwycclientreels/book/quick/open`

---

### 2. **Episode List** (dari `/chapter/list`)

**Akan di-extract per episode:**
- ✅ `chapterId` - ID unik episode
- ✅ `chapterIndex` - Nomor episode (1, 2, 3, ...)
- ✅ `chapterName` - Nama episode (contoh: "Episode 001")
- ✅ `duration` - Durasi video (detik)
- ✅ `videoWidth` - Resolusi width
- ✅ `videoHeight` - Resolusi height

**Endpoint**: `https://api.myshort.click/hwycclientreels/chapter/list`

---

### 3. **Video URLs** (dari `/chapter/load`) ⭐ PENTING!

**Akan di-extract:**
- ✅ `videoUrl` - Direct HLS playlist URL
- ✅ `token` - Access token untuk playback
- ✅ `resolution` - Quality (480p, 720p, 1080p)
- ✅ Full .m3u8 URL yang bisa langsung diplay

**Endpoint**: `https://api.myshort.click/hwycclientreels/chapter/load`

**Format URL yang di-dapat:**
```
https://stream-hw.video.shortlovers.id/.../index.m3u8?token=xxx
```

---

### 4. **Cover Images** (dari CDN requests)

**Akan di-extract:**
- ✅ Cover portrait (poster)
- ✅ Cover landscape (thumbnail)
- ✅ Multiple resolutions (jika ada)

**CDN**: `https://cdn-hw.video.shortlovers.id/`

---

## 📊 SUMMARY PER DRAMA

Dari 1 drama, scripts akan extract:

```json
{
  "bookId": "31001268925",
  "title": "Cinta di Waktu yang Tepat",
  "description": "Drama tentang...",
  "episodeCount": 78,
  "coverUrl": "https://cdn-hw.video...",
  "episodes": [
    {
      "chapterId": "100012689250001",
      "index": 1,
      "name": "Episode 001",
      "duration": 89,
      "videoUrl": "https://stream-hw.video.../index.m3u8?token=xxx"
    },
    // ... 77 episodes lagi
  ]
}
```

---

## 🎯 TARGET CAPTURE (untuk 10 dramas)

**Expected data:**
- ✅ **10 dramas** dengan complete metadata
- ✅ **700-900 episodes** total (avg 70-90 per drama)
- ✅ **700-900 video URLs** (1 per episode)
- ✅ **10-20 cover images**

---

## ⚠️ CRITICAL ACTIONS untuk Capture LENGKAP

**SAAT CAPTURE, LAKUKAN:**

1. **Tap drama** → wait 2 sec
   - ✅ Triggers `/book/quick/open` (metadata)
   
2. **Scroll episode list** → wait 2 sec
   - ✅ Triggers `/chapter/list` (episodes)
   
3. **Play episode 1 video** → **WAIT 10-15 DETIK** ⭐
   - ✅ Triggers `/chapter/load` (video URL!)
   - ✅ Triggers HLS playlist download
   - ✅ Triggers video segments download
   
4. **Back to home**
   - ✅ Ready untuk drama berikutnya

---

## 🔍 VALIDATION SETELAH CAPTURE

Script `batch_har_processor.py` akan validate:

```
✅ Drama metadata found: 10/10
✅ Episode lists found: 10/10
✅ Video URLs found: 783/783 episodes
✅ Covers found: 10/10
```

Kalau ada yang missing, script akan report dan kamu bisa re-capture drama yang kurang.

---

## 💾 OUTPUT AKHIR

**File struktur:**
```
extracted_data/
├── Cinta_di_Waktu_yang_Tepat/
│   ├── metadata.json          # ✅ Complete drama info
│   ├── cover.jpg              # ✅ Drama poster
│   └── episodes/
│       ├── episode_001.json   # ✅ Video URL + metadata
│       ├── episode_002.json
│       └── ... (78 files)
├── Drama_Kedua/
│   └── ... (same struktur)
└── ... (10 dramas total)
```

**Ready untuk import ke database!**

# 🚀 QUICK START - GoodShort Production System

## ✨ What You Got

**Complete automated scraping system** that gets:
- ✅ Real drama titles (tidak pakai angka lagi!)
- ✅ Real covers from GoodShort CDN
- ✅ Complete metadata (genre, description, author, tags)
- ✅ Auto token refresh (no manual work)
- ✅ One-click execution

---

## 🎯 How to Use (3 Steps)

### Step 1: Run Pipeline

```cmd
cd d:\kingshortid\scripts\goodshort-scraper
.\production-pipeline.bat
```

**Pilih option 2:** "Capture Metadata + Covers"

### Step 2: Browse App

Frida akan buka app otomatis, lalu:
1. Browse 10-15 drama (Popular/Trending)
2. Tap drama untuk lihat detail
3. Scroll episode list
4. Ketik `status()` untuk cek progress
5. Ketik `save()` ketika selesai
6. Press Ctrl+C

### Step 3: Process Data

```cmd
.\production-pipeline.bat
```

**Pilih option 3:** "Process Data + Download Covers"

---

## 📂 Output

```
production_output/
├── final_metadata.json    ← Import ini ke database
└── covers/                ← Copy ke backend/public/covers/
```

---

## 🎬 Import ke Database

### Copy covers dulu:

```bash
xcopy production_output\covers\* d:\kingshortid\backend\public\covers\ /Y
```

### Buat custom import script:

```javascript
// d:\kingshortid\backend\scripts\import-goodshort.js
const metadata = require('../../../scripts/goodshort-scraper/production_output/final_metadata.json');

async function importDramas() {
  for (const [bookId, drama] of Object.entries(metadata)) {
    await prisma.drama.create({
      data: {
        sourceId: drama.bookId,
        source: 'goodshort',
        title: drama.title,
        description: drama.description,
        cover: drama.cover,
        genre: drama.genre,
        category: drama.category,
        language: drama.language,
        totalEpisodes: drama.totalEpisodes,
        // ... add other fields
      }
    });
    
    console.log(`✅ Imported: ${drama.title}`);
  }
}

importDramas();
```

---

## 🔧 Commands During Capture

Ketik di Frida console:

```javascript
status()  // Lihat statistik
list()    // List semua drama yang di-capture
save()    // Force save to file
```

---

## ✅ What Makes This Different

### SEBELUM:
```
❌ "Drama 31000908479" (angka)
❌ Cover salah (screenshot)
❌ Token manual
❌ Metadata kosong
```

### SEKARANG:
```
✅ "Si Manis yang Tak Bisa Jauh" (real title!)
✅ Cover asli dari CDN
✅ Token auto-refresh
✅ Metadata lengkap 15+ fields
```

---

## 🎯 Pro Tips

1. **First time?** Run option 1 dulu (Extract Tokens)
2. **Browse banyak:** Lebih banyak = lebih banyak data
3. **Save sering:** Ketik `save()` every 5-10 dramas
4. **Check progress:** Ketik `status()` untuk monitor
5. **Wait for API:** Tunggu 2-3 detik setelah tap drama

---

## 📊 Expected Results

Setelah browse 10 dramas:

```
Total Dramas:       10
Complete Metadata:  8-9 ✅
Covers Downloaded:  10 ✅
Missing Titles:     1-2 (rare)
```

---

## 🚀 Ready in 15 Minutes!

**Total time from start to production:**
- Step 1: Run pipeline (1 min)
- Step 2: Browse app (10 min)
- Step 3: Process data (2 min)
- Step 4: Import to DB (2 min)

**= 15 minutes untuk dapat metadata production-ready!**

---

## 💬 Need Help?

**If Frida not working:**
```bash
pip install frida-tools
```

**If no data captured:**
- Clear app cache (not data!)
- Restart script
- Browse different dramas

**If covers not downloading:**
- Check internet connection
- Rerun step 3

---

## 📝 Files Reference

| File | Purpose |
|------|---------|
| `production-pipeline.bat` | Main launcher (use this!) |
| `frida/auto-token-extractor.js` | Auto token management |
| `frida/production-scraper.js` | Metadata + cover capture |
| `production_processor.py` | Cover downloader + metadata generator |
| `PRODUCTION-SYSTEM.md` | Complete documentation |

---

## ✨ That's It!

Sekarang tinggal:
1. Run `production-pipeline.bat`
2. Browse drama di app
3. Import hasil ke database
4. **DONE!** 🎉

**No more manual work. No more placeholders. Production quality!** 🚀

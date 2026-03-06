# HAR Capture with Video URLs - Quick Guide

**Goal**: Capture 10 dramas dengan COMPLETE data (metadata + video URLs) dalam 20-30 menit

---

## Setup (5 menit)

1. **Buka HTTP Toolkit** di PC
2. **Connect GoodShort app** (Android/LDPlayer)
   - Fresh start → tap "Intercept" → pilih "Android device via ADB"
   - Atau kalau udah connect: cek ada requests di HTTP Toolkit
3. **Clear previous capture** (button "Clear" di HTTP Toolkit)

---

## Workflow Per Drama (2-3 menit each)

**IMPORTANT**: Kali ini kita **HARUS PLAY VIDEO** supaya video URLs ter-capture!

### Step-by-Step:

1. **Tap drama** dari home screen
2. **WAIT 2-3 detik** (biar book metadata API ter-call)
3. **Scroll episode list** (trigger chapter list API)
4. **Tap episode 1** 
5. ⭐ **PLAY VIDEO selama 10-15 detik** ⭐ (INI YANG PENTING!)
6. **Back** ke drama detail
7. **Back** ke home
8. **Next drama** → ulangi

### Key Point:
**Step 5 adalah KUNCI!** Play video 10-15 detik akan trigger:
- Video URL request (`/chapter/load`)
- HLS manifest download
- Video segment URLs

---

## After Capturing 10 Dramas (20-30 mins total)

1. **Save HAR file**:
   - HTTP Toolkit → Menu → Export → Save as HAR
   - Filename: `batch_02.har`
   - Location: `D:\kingshortid\scripts\goodshort-scraper\har_files\`

2. **Process automatically**:
   ```bash
   cd D:\kingshortid\scripts\goodshort-scraper
   python batch_har_processor.py
   ```

3. **Import to database**:
   ```bash
   python direct_import.py
   ```

**DONE!** 10 dramas dengan complete video URLs imported! 🎉

---

## Expected Results

**From HAR**:
- ✅ Book metadata (titles, descriptions, covers)
- ✅ Episode lists (all episodes per drama)
- ✅ Video URLs (from video playback)
- ✅ HLS playlists and segment URLs

**In Database**:
- 10 new dramas
- ~700-800 episodes
- All with playable video URLs

---

## Tips

- **Don't rush** - wait 2-3 sec between actions untuk kasih API time to load
- **Play full 10-15 sec** - jangan skip video terlalu cepat
- **Check HTTP Toolkit** - should see ~50-100 requests per drama
- **Target**: 10 dramas in 20-30 mins (dapat 700+ episodes!)

---

## Troubleshooting

**Q: Video not playing?**
- Check internet connection
- Close/reopen GoodShort app
- Reconnect HTTP Toolkit

**Q: HAR file too big?**
- Normal! Expect 200-500 MB untuk 10 dramas
- File size is good = more data captured

**Q: Lupa play video?**
- No problem! That drama won't have video URLs
- Can re-capture later or skip for now

---

## Ready?

1. Open HTTP Toolkit
2. Connect GoodShort
3. Clear previous capture
4. Start browsing + playing videos!

**Notify me when HAR saved!** 📁

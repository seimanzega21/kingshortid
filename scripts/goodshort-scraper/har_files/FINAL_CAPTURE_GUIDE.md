# 🎯 COMPLETE CAPTURE GUIDE - 30 Minutes to 10 Dramas!

**Ready to capture?** Follow this simple workflow!

---

## 📋 PRE-FLIGHT CHECKLIST

**Before starting:**
- [ ] HTTP Toolkit is open
- [ ] GoodShort app connected to HTTP Toolkit
- [ ] Previous captures cleared (button "Clear")
- [ ] Timer ready (~30 mins total)

---

## 🎬 CAPTURE WORKFLOW

### **Per Drama** (~2-3 minutes each):

1. **Tap drama** from home feed
   - ⏱️ Wait 2-3 seconds
   - ✅ Triggers `/book/quick/open` (metadata)

2. **Scroll episode list** slowly
   - ⏱️ Wait 2 seconds
   - ✅ Triggers `/chapter/list` (episodes)

3. **Tap Episode 1** to open player
   - ⏱️ Wait for player to load

4. **▶️ PLAY VIDEO** - **WAIT 10-15 SECONDS** ⭐ **CRITICAL!**
   - ✅ Triggers `/chapter/load` (VIDEO URL!)
   - ✅ Triggers HLS playlist download
   - ✅ Downloads video segments
   - **DON'T SKIP THIS!** Video must actually play!

5. **Back** to drama detail → **Back** to home
   - Ready for next drama!

---

## ⏱️ TIME BREAKDOWN

- **Drama 1-5**: 15 minutes (2-3 mins each)
- **Quick break**: 2 minutes (check HTTP Toolkit)
- **Drama 6-10**: 15 minutes
- **Total**: ~32 minutes

---

## 🎯 TARGET: 10 DRAMAS

**Expected capture:**
- ✅ 10 dramas with metadata
- ✅ ~700-900 episodes
- ✅ ~700-900 video URLs (from `/chapter/load`)
- ✅ 10+ covers

---

## 💾 AFTER CAPTURE

### **Step 1: Save HAR**
1. HTTP Toolkit → Menu (⋮) → Export
2. Format: **HAR (HTTP Archive)**
3. Filename: `batch_02.har`
4. Location: `D:\kingshortid\scripts\goodshort-scraper\har_files\`
5. Click **Save**

### **Step 2: Process HAR**
```bash
cd D:\kingshortid\scripts\goodshort-scraper
python complete_har_processor.py har_files/batch_02.har
```

**Output:**
```
✅ Dramas found: 10
✅ Episodes found: 783
✅ Video URLs found: 783
✅ Covers found: 10

💾 Saved to: extracted_data/batch_02_extracted.json
✅ Also saved 10 individual drama folders
```

### **Step 3: Import to Database**
```bash
python direct_import.py
```

**Done!** 🎉

---

## ✅ VALIDATION CHECKLIST

After processing, verify:
- [ ] All 10 dramas extracted
- [ ] Each drama has 70-90 episodes
- [ ] Each episode has `videoUrl` field
- [ ] Video URLs start with `https://stream-hw.video.shortlovers.id/`
- [ ] Covers downloaded

---

## ⚠️ CRITICAL: WHY 10-15 SECONDS VIDEO PLAYBACK?

**Short answer:** `/chapter/load` only triggers when video actually starts playing!

**If you skip video:**
- ❌ No `/chapter/load` request
- ❌ No video URL captured
- ❌ Episodes will have `videoUrl: null`
- ❌ Can't import to database

**Solution:** ALWAYS play video 10-15 seconds per drama!

---

## 🔧 TROUBLESHOOTING

**Q: Video not playing?**
- Check internet connection
- Restart GoodShort app
- Reconnect HTTP Toolkit

**Q: HAR file too big?**
- Normal! 200-500 MB for 10 dramas
- Large file = more data captured (good!)

**Q: Forgot to play video for some dramas?**
- Re-capture those specific dramas later
- Or continue with next batch

**Q: HTTP Toolkit shows no requests?**
- Reconnect app: HTTP Toolkit → Android device via ADB
- Check ADB: `adb devices` should show device

---

## 📊 WHAT GETS CAPTURED

From each request type:

### `/book/quick/open`
```json
{
  "bookId": "31001268925",
  "name": "Cinta di Waktu yang Tepat",
  "description": "Drama tentang...",
  "chapterCount": 78,
  "largeCover": "https://cdn-hw..."
}
```

### `/chapter/list`
```json
{
  "list": [
    {
      "id": "100012689250001",
      "index": 1,
      "chapterName": "Episode 001",
      "playTime": 89
    }
  ]
}
```

### `/chapter/load` ⭐
```json
{
  "videoUrl": "https://stream-hw.video.shortlovers.id/.../index.m3u8?token=xxx"
}
```

---

## 🚀 READY TO START?

1. ✅ Open HTTP Toolkit
2. ✅ Clear previous capture
3. ✅ Start timer
4. ✅ Begin capturing!

**Remember:** PLAY VIDEO 10-15 seconds per drama! ⭐

**Good luck!** 🎬

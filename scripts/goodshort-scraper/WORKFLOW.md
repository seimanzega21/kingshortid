# GoodShort Scraping Workflow

## Current Status ✅

### Completed
- [x] Frida capture script running (PID: 9224)
- [x] 1 Drama captured: 31000908479
- [x] 1 Episode downloaded: 411618 (5.8MB MP4)
- [x] Video segments successfully merged with ffmpeg

### Ready to Continue
- [ ] Capture more dramas (target: 5-10 dramas)
- [ ] Download all captured episodes
- [ ] Import to KingShortID database

---

## Quick Start Guide

### Step 1: Capture More Episodes 📱

**Frida is ALREADY RUNNING** - Just browse the GoodShort app!

1. Open GoodShort app on your phone/emulator
2. Browse different dramas
3. Open each episode (tap to play, Frida will auto-capture)
4. The terminal will show: `📺 Episode X captured`

**To check progress in Frida console:**
```javascript
status()   // See how many dramas/episodes captured
list()     // List all dramas
export()   // Get JSON to save
```

### Step 2: Export Captured Data 💾

When you've captured enough episodes:

1. In Frida terminal, type:
   ```javascript
   exportData()
   ```

2. Copy the JSON output

3. **Replace** `captured-episodes.json` with the new JSON

### Step 3: Download All Videos 📥

Run the batch download script:

```bash
cd d:\kingshortid\scripts\goodshort-scraper
npx ts-node src/batch-download.ts
```

This will:
- Download all video segments for each episode
- Merge them into MP4 files
- Save to `downloads/{bookId}/episode_{chapterId}.mp4`

### Step 4: Verify Downloads ✅

Check the `downloads` folder for completed MP4 files:

```bash
dir downloads\*\*.mp4
```

---

## File Structure

```
downloads/
├── 31000908479/              # Drama folder (bookId)
│   ├── cover.jpg             # Drama cover image
│   ├── episode_411618.mp4    # Complete episode
│   └── chapter_411618/       # Raw segments (can delete after merge)
│       ├── segment_000000.ts
│       ├── segment_000001.ts
│       └── ...
```

---

## Tips & Tricks 💡

### Fast Capture Strategy
1. Go to drama's episode list
2. Tap each episode quickly (just open, 1 second each)
3. Frida captures the URL instantly
4. No need to watch full videos

### Recommended Dramas to Target
- Popular dramas with many episodes
- High-quality content (720p)
- Complete seasons

### Troubleshooting
- **Frida stopped?** Re-run: `frida -U -f com.newreading.goodreels -l frida\capture-autosave.js`
- **ffmpeg error?** Install: `choco install ffmpeg`
- **Download fails?** Check internet connection, videos are ~5-30MB each

---

## Next Steps (After Scraping)

Once you have 5-10 dramas downloaded:

1. **Create import script** to map GoodShort data to KingShortID schema
2. **Upload videos** to Cloudflare R2
3. **Import metadata** to PostgreSQL database
4. **Test** in KingShortID mobile app

---

## Current Capture Data

```json
{
  "dramas": {
    "31000908479": {
      "bookId": "31000908479",
      "title": "Drama 1 (Captured)",
      "cover": "https://acf.goodreels.com/videobook/31000908479/202509/cover-pP6DgqN9ro.jpg",
      "episodes": {
        "411618": {
          "chapterId": "411618",
          "token": "vm7tuebria",
          "videoId": "7o2ifsxecm",
          "resolution": "720p"
        }
      }
    }
  },
  "lastUpdate": "2026-01-31T18:06:00Z"
}
```

**Action Required:** Capture more episodes by browsing the GoodShort app! 🎬

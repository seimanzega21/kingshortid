# IMPROVED HAR Capture Instructions - Batch 1 (v2)

## Critical: Capture Book Metadata!

Previous capture got episode data but MISSED book/drama metadata. This time we focus on **drama detail pages**.

---

## Setup
1. **Delete old HAR**: `batch_01.har` (optional, will overwrite)
2. **Open HTTP Toolkit** → Connect GoodShort app
3. Start fresh capture

---

## NEW Workflow - Per Drama (10 dramas)

### For EACH drama (~3 mins each):

1. **From home screen** → Tap drama card
   - ⏱️ **WAIT 2-3 seconds** (let detail page load completely)
   
2. **On detail page**:
   - Scroll down to see episode list
   - ⏱️ **WAIT 2 seconds** (let episode list load)
   
3. **Tap Episode 1** → Play video
   - ⏱️ **WAIT 5 seconds** (let video load)
   
4. **Back** to drama detail
   - ⏱️ **WAIT 1 second**
   
5. **Back** to home screen
   - Ready for next drama

### Key Changes from Before:
- ✅ **Wait on detail page** (this triggers book metadata API)
- ✅ **Wait on episode list** (this triggers chapter list API)
- ✅ **Wait on video** (this triggers video URL API)

**Total time**: ~30 minutes for 10 dramas

---

## Dramas to Capture

Pick 10 diverse dramas:
- ✅ Mix of genres (romance, action, drama, CEO, etc.)
- ✅ Mix of lengths (short 20-ep, medium 50-ep, long 90-ep)
- ✅ Indonesian language dramas
- ✅ Dramas you haven't watched yet (fresh data)

---

## After Capture

1. **Stop HTTP Toolkit**
2. **Export HAR**:
   - File → Export HAR
   - Save location: `D:\kingshortid\scripts\goodshort-scraper\har_files\`
   - Filename: `batch_01_v2.har` (or overwrite `batch_01.har`)
3. **Notify me** when done

---

## Expected File Size

Good capture should be **100-500 MB** depending on:
- Number of dramas
- Video quality captured
- How long videos played

If file is <50MB, probably incomplete capture.

---

## Troubleshooting

**If HTTP Toolkit shows no traffic**:
- Restart HTTP Toolkit
- Reconnect Android device
- Make sure GoodShort app is using HTTP Toolkit proxy

**If capture seems slow**:
- Normal! Each API call takes 1-2 seconds
- Don't rush, wait times are important

---

## Ready to Start?

Follow the workflow above carefully. The key is **waiting on drama detail page** to ensure book metadata loads!

Good luck! 🎬

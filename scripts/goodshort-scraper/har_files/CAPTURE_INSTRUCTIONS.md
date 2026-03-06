# HAR Capture Instructions - Batch 1

## Setup
1. **Open HTTP Toolkit** di PC
2. **Connect Android device/emulator**:
   - Pilih "Android device via ADB"
   - Pastikan GoodShort app sudah installed
3. HTTP Toolkit akan start capturing

## Capture Session (Target: 10 Dramas)

### Step-by-Step:
1. **Open GoodShort app** di device
2. **Browse dramas** dari home screen
3. **Per drama**:
   - Tap drama card → opens detail page (captures metadata)
   - Scroll down episode list (captures episode data)
   - Play episode 1 for ~1-2 seconds (captures video URL)
   - Back to home
   - Repeat for next drama

### Tips:
- ⏱️ ~2-3 minutes per drama
- 🎯 Total time: ~20-30 minutes for 10 dramas
- 📝 Keep track of drama titles you browse
- 🔄 If app crashes, continue from where you left off

### Drama Selection Strategy:
- Choose dramas with different episode counts (short/medium/long)
- Mix popular and less popular dramas
- Test variety of genres

## Saving HAR File

1. **Stop capturing** di HTTP Toolkit
2. **Export HAR**:
   - Click "Export" button
   - Choose location: `D:\kingshortid\scripts\goodshort-scraper\har_files\`
   - Filename: `batch_01.har`
3. **Save**

## Ready for Processing

After saving HAR file, run:
```bash
cd D:\kingshortid\scripts\goodshort-scraper
python batch_har_processor.py --har-file har_files\batch_01.har --output r2_ready
```

---

## Checklist
- [ ] HTTP Toolkit connected to GoodShort app
- [ ] Browsed 10 dramas (noted titles)
- [ ] Each drama: viewed detail + episode list + played 1 episode
- [ ] Exported HAR to `har_files/batch_01.har`
- [ ] Ready to run batch processor

---

**Estimated capture time**: 20-30 minutes
**Expected HAR file size**: 5-20 MB

Good luck! 🚀

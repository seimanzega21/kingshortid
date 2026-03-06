# HTTP TOOLKIT - Step-by-Step Checking Guide

## 📋 Checklist untuk Cek HTTP Toolkit

### Step 1: Verify HTTP Toolkit Connected ✅

**Di HTTP Toolkit window:**
- Look for status bar at top
- Should show: **"Intercepting: Android device"** dengan ikon hijau
- Or: **"Intercepting: emulator-5554"**

**If NOT connected:**
1. Click "Android Device via ADB" again
2. Wait 10-15 seconds
3. Check emulator for certificate prompt

---

### Step 2: Play Episode di Emulator 📺

**In Android Studio emulator:**
1. Open GoodShort app
2. Navigate to any drama (misal: "Jeratan Hati")
3. Tap Episode 1
4. **Tap PLAY button** (sangat penting!)
5. **Biarkan play minimal 30 detik**
6. Don't pause, don't skip - just let it buffer

---

### Step 3: Check HTTP Toolkit Requests 🔍

**Di HTTP Toolkit main window:**

**Look for 3 hal:**

#### A. Total Requests Count
- Bottom of screen should show: **"X requests"**
- If playing video: should be **50-200+ requests**
- If only 5-10 requests: only API calls, no video

#### B. Request List
- Main panel shows list of ALL HTTP requests
- Scroll through list
- Look for URLs containing:
  - `goodreels.com`
  - `.ts` extension
  - `segment` in filename

#### C. Filter Test
- Click **search box** at top
- Type: `.ts`
- Press Enter
- **If SUCCESS**: List shows .ts files
- **If FAIL**: "No matching requests"

---

### Step 4: Inspect a .ts Request (If Found) 🎯

**If you see .ts files:**

1. **Click on any .ts request**
2. **Right panel shows details:**
   - **URL**: Full path to segment
   - **Status**: Should be **200 OK** (green)
   - **Size**: ~200-800 KB typically
   - **Type**: `video/MP2T` or similar
3. **Copy URL** for testing later

---

### Step 5: Visual Indicators 🎨

**SUCCESS looks like:**
```
┌─────────────────────────────────────────────────┐
│ 🟢 GET ...goodreels.com/.../segment_000000.ts  │
│    Status: 200  Size: 455 KB  Time: 234ms      │
├─────────────────────────────────────────────────┤
│ 🟢 GET ...goodreels.com/.../segment_000001.ts  │
│    Status: 200  Size: 512 KB  Time: 187ms      │
├─────────────────────────────────────────────────┤
│ 🟢 GET ...goodreels.com/.../segment_000002.ts  │
│    Status: 200  Size: 498 KB  Time: 201ms      │
└─────────────────────────────────────────────────┘

Total: 50+ .ts requests (GOOD!)
```

**FAILURE looks like:**
```
┌─────────────────────────────────────────────────┐
│ 🟢 GET api.goodshort.com/v1/drama/detail       │
│ 🟢 GET api.goodshort.com/v1/episodes          │
│ 🟢 GET cdn.goodshort.com/cover.jpg            │
└─────────────────────────────────────────────────┘

Total: 5-10 requests only (NO VIDEO)
```

---

## 🐛 Troubleshooting

### Issue 1: "No requests at all"
**Solution:**
- HTTP Toolkit not intercepting
- Restart connection: Click "Android Device via ADB" again
- Check emulator network: `adb shell settings get global http_proxy`

### Issue 2: "Only API calls, no .ts files"
**Possible causes:**
1. **SSL Pinning** - App blocks MITM
2. **Certificate not trusted** - Check Android settings
3. **Video didn't buffer** - Play longer (60 seconds)

**Try:**
```bash
# Disable SSL pinning with Frida
frida -U -n "GoodShort" --codeshare akabe1/frida-multiple-unpinning
```

### Issue 3: ".ts files but status 403"
**Meaning:**
- HTTP Toolkit CAN see requests ✅
- But CDN blocks the actual download ❌

**Solution:**
- Export HAR anyway
- Use URLs with custom headers
- Or proceed with screenrecord method

---

## ✅ Success Criteria

HTTP Toolkit test is **SUCCESSFUL** if:
- [x] Intercepting status active
- [x] Episode played for 30+ seconds
- [x] Filter `.ts` shows results
- [x] Status codes are 200 OK
- [x] File sizes are 200KB-1MB each

---

## 📤 If Successful - Export Steps

1. **File → Export** (top menu)
2. **Choose format**: HAR
3. **Save as**: `goodshort_capture.har`
4. **Location**: `d:\kingshortid\scripts\goodshort-scraper\`
5. **Parse**: `python parse_toolkit_export.py goodshort_capture.har`

---

## 📊 What To Report Back

**Please tell me:**

**A. Connection Status?**
- Connected / Not connected

**B. Played video for how long?**
- Seconds played: ___

**C. Total requests shown?**
- Number: ___

**D. Filter `.ts` result?**
- Found X files / Found 0 files

**E. Status codes?**
- 200 OK / 403 Forbidden / Other

Based on answers, saya bisa bantu next steps! 🚀

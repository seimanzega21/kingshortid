# HTTP TOOLKIT - Quick Setup Guide

## 🎯 Goal
Capture actual .ts segment URLs when video plays

## 📥 Download & Install

**Windows:**
```
https://httptoolkit.com/
→ Download for Windows
→ Run installer
```

## 🚀 Quick Start (5 minutes)

### 1. Launch HTTP Toolkit
- Open HTTP Toolkit app
- Main screen shows interception options

### 2. Connect Android Device
- Click **"Android Device via ADB"**
- HTTP Toolkit will:
  - Install CA certificate
  - Configure proxy automatically
  - Show "Intercepting Android device" ✅

### 3. Verify Connection
- You should see:
  ```
  ✅ Intercepting: Android device
  📱 Device: [Your device name]
  ```

## 🧪 Test Episode Playback

### Manual Test Flow:
1. **Open GoodShort** on Android
2. **Navigate** to "Jenderal Jadi Tukang"
3. **Tap Play** on Episode 1
4. **Wait** 30 seconds (let it buffer)

### What to Look For in HTTP Toolkit:

**Success Indicators** ✅:
```
Request URL: https://v2-akm.goodreels.com/.../segment_000000.ts
Method: GET
Status: 200 OK
Type: video/MP2T
Size: ~500 KB
```

**You should see**:
- Multiple `.ts` requests (50-100)
- Green status codes (200)
- Video content type

**Failure Indicators** ❌:
- No `.ts` requests visible
- Only see app API calls
- Certificate warnings

## 📊 What Success Looks Like

### Expected Traffic Pattern:
```
1. GET playlist.m3u8        (playlist)
2. GET segment_000000.ts    (video chunk 1)
3. GET segment_000001.ts    (video chunk 2)
4. GET segment_000002.ts    (video chunk 3)
... (continues for ~50-100 segments)
```

### Screenshot Example:
HTTP Toolkit view should show:
```
┌─────────────────────────────────────────────┐
│ 🟢 GET segment_000000.ts    200  455 KB     │
│ 🟢 GET segment_000001.ts    200  512 KB     │
│ 🟢 GET segment_000002.ts    200  498 KB     │
│ 🟢 GET segment_000003.ts    200  501 KB     │
└─────────────────────────────────────────────┘
```

## 🎛️ Filter Settings

To see only video segments:

1. Click **"Filter"** in HTTP Toolkit
2. Add filter:
   ```
   URL contains: .ts
   Domain: goodreels.com
   ```

## 📤 Export Captured Data

If test successful:

1. **File → Export**
2. **Select Format**: HAR (recommended)
3. **Save as**: `captured_requests.har`
4. **Location**: `d:\kingshortid\scripts\goodshort-scraper\`

## 🐛 Troubleshooting

### Issue: No .ts files visible

**Solution 1**: App using certificate pinning
```bash
# Disable SSL pinning with Frida
frida -U -n "GoodShort" --codeshare akabe1/frida-multiple-unpinning
```

**Solution 2**: Reinstall certificate
```
HTTP Toolkit → Android Device → Reinstall
```

**Solution 3**: Check proxy settings
```bash
adb shell settings get global http_proxy
# Should show: <PC_IP>:8080
```

### Issue: Certificate not trusted

**Fix on Android**:
1. Settings → Security
2. Trusted credentials → User
3. Find "HTTP Toolkit CA"
4. Enable if disabled

### Issue: App crashes on startup

**Likely**: SSL pinning is blocking proxy

**Solution**: Combine with Frida unpinning:
```bash
# Terminal 1: HTTP Toolkit
# Terminal 2:
frida -U -n "GoodShort" -l frida\ssl-unpinning.js
```

## ✅ Success Criteria

You're ready to proceed if:
- [x] HTTP Toolkit shows "Intercepting" status
- [x] Can see `.ts` segment requests
- [x] Status codes are 200 OK
- [x] Segments download (green in toolkit)

## 🚀 Next Steps After Success

1. Run full automation:
   ```bash
   .\capture_with_toolkit.bat
   ```

2. Script will:
   - Auto-play 20 episodes
   - HTTP Toolkit captures all .ts URLs
   - Export to HAR file
   - Parse URLs
   - Download segments
   - Upload to R2

3. Estimated time: **2-3 hours for complete drama**

## 📝 Notes

- HTTP Toolkit is **free** and open source
- Works on Windows, Mac, Linux
- Alternative: **mitmproxy** (CLI tool)
- Charles Proxy also works (paid)

---

**Ready?** Press any key in the test script after setup!

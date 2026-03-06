# Connect HTTP Toolkit to Android Studio Emulator

## ✅ Current Status

![Android Studio Emulator Running](file:///C:/Users/Seiman/.gemini/antigravity/brain/24dfc429-2289-4f60-98c3-401243ccd5cd/uploaded_media_1769942254234.png)

**Perfect setup!**
- ✅ Pixel 5 (API 30) emulator running
- ✅ GoodShort app installed and working
- ✅ Ready for MITM interception!

---

## 🔌 Connection Steps

### Method 1: HTTP Toolkit (Recommended for Testing)

**Step 1: Identify Emulator ADB ID**
```bash
adb devices
```
Expected output:
```
List of devices attached
emulator-5554    device    <-- Your emulator
```

**Step 2: Connect HTTP Toolkit**

1. In HTTP Toolkit, click **"Android Device via ADB"**
2. HTTP Toolkit will:
   - Detect `emulator-5554`
   - Install certificate
   - Configure proxy
3. Wait for "Intercepting Android device" ✅

**Step 3: Test Interception**

1. In emulator, tap **any drama** (e.g., "Jeratan Hati")
2. Tap **Play** on Episode 1
3. Let video play for 30 seconds

**Step 4: Verify in HTTP Toolkit**

Look for:
```
🟢 GET https://v2-akm.goodreels.com/.../segment_000000.ts
   Status: 200 | Size: ~500 KB | Type: video/MP2T
```

---

### Method 2: mitmproxy (For Full Automation)

**Quick Setup:**
```bash
# 1. Get your PC IP
ipconfig
# Note your IPv4 address (e.g., 192.168.1.100)

# 2. Configure emulator proxy
adb -s emulator-5554 shell settings put global http_proxy 192.168.1.100:8080

# 3. Start mitmproxy with auto-save
mitmdump -s mitm_video_dumper.py
```

**Install Certificate on Emulator:**
1. In emulator browser, go to: `http://mitm.it`
2. Download "Android" certificate
3. Install it:
   - Settings → Security → Install from storage
   - Select downloaded cert
   - Name it "mitmproxy CA"

**Test:**
1. Play video in GoodShort
2. Check terminal - should see:
   ```
   🎬 NEW EPISODE DETECTED: 614590
   📺 Episode 614590: Saved 10 segments
   📺 Episode 614590: Saved 20 segments
   ```

---

## 🚀 Quick Test (RIGHT NOW!)

**Fastest way to test:**

```bash
# Option A: HTTP Toolkit (Visual)
1. Click "Android Device via ADB" in HTTP Toolkit
2. Play 1 episode in emulator
3. Check if .ts files appear in HTTP Toolkit

# Option B: mitmproxy (Automated)
mitmdump -s mitm_video_dumper.py
# Then play episode, watch terminal for saves
```

---

## 📊 What Success Looks Like

### HTTP Toolkit:
```
Intercepting: Android device (emulator-5554)

Requests:
├── GET playlist.m3u8           200 OK
├── GET segment_000000.ts       200 OK (455 KB)
├── GET segment_000001.ts       200 OK (512 KB)
└── GET segment_000002.ts       200 OK (498 KB)
```

### mitmproxy:
```
============================================================
🎬 NEW EPISODE DETECTED: 614590
============================================================

📺 Episode 614590: Saved 10 segments (4.8 MB)
📺 Episode 614590: Saved 20 segments (9.5 MB)
...
📺 Episode 614590: Saved 50 segments (24.1 MB)
```

---

## 🎯 After Success

If segments are captured successfully:

**1. Full Automation:**
```bash
.\mitm-full-auto.bat
```
Will auto-play 20 episodes and save all segments!

**2. Organize & Upload:**
```bash
python organize_segments.py
python upload_to_r2.py
```

---

## 🐛 Troubleshooting

### Issue: "No devices found"
```bash
# Make sure emulator is running
adb devices

# Should show: emulator-5554
```

### Issue: Certificate not trusted
In emulator:
1. Settings → Security
2. Trusted credentials → User
3. Verify certificate is there

### Issue: App won't open after proxy setup
```bash
# Disable proxy temporarily
adb shell settings put global http_proxy :0

# Retry certificate install
```

---

## 💡 Pro Tip - Emulator Advantages

Compared to physical device:
- ✅ **Faster** ADB access
- ✅ **Easier** certificate install
- ✅ **Better** automation control
- ✅ **No battery** concerns!

Android Studio emulator is PERFECT for this! 🎉

---

## ⏭️ Next Step

**Just try it!**

Pick ONE method:
- **Visual learner?** → HTTP Toolkit
- **Want automation?** → mitmproxy

Then play 1 episode and see if .ts files get captured!

Ready? 🚀

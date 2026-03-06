# HTTP Toolkit Setup Guide untuk GoodShort Scraping

## 🎯 Langkah Setup

### 1. Install HTTP Toolkit
- Download: https://httptoolkit.com/
- Install dengan default settings
- **PENTING**: HTTP Toolkit akan auto-install certificate ke LDPlayer

### 2. Connect HTTP Toolkit ke LDPlayer

**Di HTTP Toolkit:**
1. Buka HTTP Toolkit desktop app
2. Klik **"Android device via ADB"**
3. HTTP Toolkit akan auto-detect LDPlayer
4. Certificate akan auto-installed (no manual work!)
5. Status harus: **"Connected to [device]"**

**Jika tidak auto-detect:**
```powershell
# Manual ADB connect
adb connect 127.0.0.1:5555
adb devices
# Lalu coba lagi "Android device via ADB" di HTTP Toolkit
```

### 3. Verify Connection

**Di LDPlayer:**
- Buka Settings → Wi-Fi → Long press WiFi → Proxy
- Pastikan muncul HTTP Toolkit proxy

**Test Connection:**
- Buka Chrome di LDPlayer
- Browse ke http://example.com
- HTTP Toolkit harus tampilkan request

### 4. Capture GoodShort Traffic

**PENTING - Keuntungan HTTP Toolkit:**
- ✅ Auto SSL bypass untuk most apps
- ✅ Certificate auto-installed (unlike mitmproxy)
- ✅ Visual UI untuk filter requests
- ✅ Easy export to HAR

**Steps:**
1. **Pastikan** HTTP Toolkit status "Intercepting"
2. Buka GoodShort di LDPlayer
3. Browse 2-3 drama:
   - Scroll home feed
   - Klik drama detail
   - Buka episode list
   - Play 1-2 episode
4. **Monitor** di HTTP Toolkit - filter "goodreels" atau "xintaicz"
5. **Export**: Pilih all requests → Export as HAR

### 5. Auto Token Refresh

Setelah export HAR:
```powershell
# Token manager akan auto extract
python token_manager.py
```

Token akan saved ke `auth_tokens.json` dan auto-refresh saat expired!

## ⚡ Quick Start Commands

```powershell
# 1. Stop mitmproxy (if running)
# Press Ctrl+C in mitmproxy terminal

# 2. Ensure ADB connected
adb connect 127.0.0.1:5555

# 3. Open HTTP Toolkit
httptoolkit

# 4. After capture, extract token
python token_manager.py

# 5. Run scraper (coming soon)
python goodshort_scraper.py
```

## 🔍 Troubleshooting

**HTTP Toolkit tidak detect LDPlayer:**
- Restart LDPlayer
- Run `adb devices` - pastikan ada device
- Coba manual connect: `adb connect 127.0.0.1:5555`

**Certificate error di app:**
- HTTP Toolkit biasanya auto-bypass
- Jika masih error, app mungkin perlu Frida (tapi rare)

**No traffic captured:**
- Check proxy di LDPlayer WiFi settings
- Restart GoodShort app
- Ensure HTTP Toolkit showing "Intercepting"

## ✅ Success Indicators

1. HTTP Toolkit shows "`Connected to ...`"
2. Browse Chrome → traffic appears
3. Open GoodShort → API requests visible
4. Export HAR → token extracted successfully

**Next:** Build production scraper dengan auto token refresh!

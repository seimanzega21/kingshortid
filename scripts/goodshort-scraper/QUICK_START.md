# GoodShort Complete Scraping - Quick Start

## 🚀 3-Step Process

### Step 1: Capture Metadata (Frida)

```bash
cd d:\kingshortid\scripts\goodshort-scraper

# Kill app
adb shell am force-stop com.newreading.goodreels

# Start Frida
frida -U -f com.newreading.goodreels -l frida\production-scraper.js --no-pause
```

**Then browse dramas in app** (scroll, tap details, view episodes)

```bash
# Pull captured data
adb pull /sdcard/goodshort_production_data.json ./scraped_data/
```

---

### Step 2: Process & Organize

```bash
# Process captured data
python process_production_capture.py

# Output will be in: r2_ready/
```

This will:
- ✅ Download covers
- ✅ Organize episodes in order (1, 2, 3...)
- ✅ Create metadata files
- ✅ Generate R2-ready structure

---

### Step 3: Download Videos (Optional - Using HTTP Toolkit)

#### 3a. Extract Headers from HTTP Toolkit

1. **Play video** in emulator (HTTP Toolkit connected)
2. **Find .ts segment** with status 200 OK
3. **Right-click** → "Copy as cURL"
4. **Save** to file `curl_export.txt`

```bash
# Parse headers
python download_with_http_toolkit.py --parse-curl curl_export.txt
```

#### 3b. Download Videos

```bash
# Download for specific drama
python download_with_http_toolkit.py --drama-folder r2_ready\jenderal_jadi_tukang
```

This will:
- ✅ Download all .ts segments
- ✅ Combine to MP4 using ffmpeg
- ✅ Save to episode folders

---

### Step 4: Upload to R2

```bash
python upload_to_r2.py
```

---

## 📋 Troubleshooting

### "No dramas found"
```bash
# Make sure you pulled data from device
adb pull /sdcard/goodshort_production_data.json ./scraped_data/
```

### "403 Forbidden" when downloading videos
- Capture fresh headers from HTTP Toolkit
- Make sure you copy **complete** cURL (all headers)
- Try different .ts segment URL

### "ffmpeg not found"
```bash
# Install ffmpeg
choco install ffmpeg

# Or download: https://ffmpeg.org/download.html
```

---

## 📊 Check Progress

```bash
# See what was captured
python process_production_capture.py --dry-run

# Check Frida status (while running)
# In Frida console type: status()
```

---

## 🎯 Full Workflow Example

```bash
# 1. Start capture
frida -U -f com.newreading.goodreels -l frida\production-scraper.js --no-pause

# 2. Browse 5-10 dramas in app, then Ctrl+C

# 3. Pull data
adb pull /sdcard/goodshort_production_data.json ./scraped_data/

# 4. Process
python process_production_capture.py

# 5. (Optional) Download videos
#    - Get cURL from HTTP Toolkit first
python download_with_http_toolkit.py --parse-curl curl_export.txt
python download_with_http_toolkit.py --drama-folder r2_ready\drama_name

# 6. Upload to R2
python upload_to_r2.py
```

---

## 📁 Output Structure

```
r2_ready/
├── jenderal_jadi_tukang/
│   ├── cover.jpg                    # Downloaded
│   ├── metadata.json                # Drama info
│   ├── episodes.json                # Episode list
│   └── episodes/
│       ├── ep_1/
│       │   ├── metadata.json        # Episode info
│       │   ├── playlist.m3u8        # HLS URL
│       │   ├── segments/            # (if downloaded)
│       │   └── video.mp4            # (if combined)
│       ├── ep_2/
│       └── ...
```

# GoodShort Video Scraper

Scrape videos from GoodShort app using Frida to intercept API requests.

## Prerequisites

1. **Python + Frida**
   ```bash
   pip install frida-tools
   ```

2. **Node.js dependencies**
   ```bash
   npm install
   ```

3. **ffmpeg** (for combining video segments)
   ```bash
   choco install ffmpeg
   ```

4. **Android Emulator** with:
   - GoodShort app installed
   - frida-server running (push to /data/local/tmp and run as root)

## Quick Start

### Step 1: Capture Episode URLs

Double-click `start-capture.bat` or run:
```bash
frida -U -p [PID] -l frida/capture-autosave.js
```

Then in the GoodShort app:
1. Browse to the dramas you want to scrape
2. Open each episode (just open, don't need to watch full video)
3. The script will display captured episodes

In Frida console:
- `status()` - See capture statistics
- `list()` - List all captured dramas  
- `exportData()` - Get JSON to save

### Step 2: Save Captured Data

Copy the JSON output from `exportData()` and save to `captured-episodes.json`

### Step 3: Download Videos

Double-click `start-download.bat` or run:
```bash
npx ts-node src/batch-download.ts captured-episodes.json
```

## Files Structure

```
goodshort-scraper/
├── frida/
│   ├── capture-autosave.js    # Main capture script
│   ├── capture-episodes.js    # Alternative capture script
│   └── hook-request.js        # Basic request logger
├── src/
│   ├── batch-download.ts      # Batch download all episodes
│   ├── download-video.ts      # Single video downloader
│   └── api-client.ts          # API client (experimental)
├── downloads/                  # Downloaded videos go here
├── captured-episodes.json      # Captured episode data
├── start-capture.bat          # Easy start capture
└── start-download.bat         # Easy start download
```

## URL Patterns Discovered

| Type | CDN | Pattern |
|------|-----|---------|
| Video | v2-akm.goodreels.com | `/mts/books/{xxx}/{bookId}/{chapterId}/{token}/720p/{videoId}_720p_{segment}.ts` |
| Cover | acf.goodreels.com | `/videobook/{YYYYMM}/cover-{id}.jpg` |
| API | api-akm.goodreels.com | `/hwycclientreels/*` |

## Notes

- Video CDN does NOT require authentication
- API requires dynamic `sign` header (timestamp-based, hard to replicate)
- Each episode has unique `token` and `videoId` - must capture from app

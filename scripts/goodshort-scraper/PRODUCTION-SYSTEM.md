# 🚀 GoodShort Production Scraping System

## Complete Solution - No Manual Work Required

This system automatically:
- ✅ Extracts and refreshes authentication tokens
- ✅ Captures **real drama titles**
- ✅ Downloads **real cover images** from GoodShort CDN
- ✅ Extracts complete metadata (description, genre, episodes, etc.)
- ✅ Generates production-ready database import scripts

---

## 📁 System Components

### 1. Auto Token Extractor
**File:** `frida/auto-token-extractor.js`

Automatically extracts authentication tokens from the app:
- User token (JWT)
- GAID (Google Advertising ID)
- Android ID
- Auto-saves to `/sdcard/goodshort_tokens.json`

### 2. Production Metadata Scraper
**File:** `frida/production-scraper.js`

Complete metadata capture:
- Real drama titles (not placeholders!)
- Real cover URLs (multiple sizes)
- Full descriptions
- Genre, category, author
- Episode lists with metadata
- Video URLs for streaming
- Auto-saves to `/sdcard/goodshort_production_data.json`

### 3. Production Processor
**File:** `production_processor.py`

Python script that:
- Downloads all cover images
- Generates final metadata JSON
- Creates SQL database import script
- Validates data completeness

### 4. Pipeline Wrapper
**File:** `production-pipeline.bat`

One-click launcher with menu:
1. Extract tokens
2. Capture metadata
3. Process data
4. Complete pipeline (all steps)

---

## 🎯 Quick Start

### Option A: Complete Pipeline (Recommended)

```bash
# Run the complete pipeline
production-pipeline.bat

# Select option 4 (Complete Pipeline)
# Follow on-screen instructions
```

### Option B: Step-by-Step

#### Step 1: Extract Tokens (First Time Only)

```bash
# Method 1: Use wrapper
production-pipeline.bat
# Select option 1

# Method 2: Manual
frida -U -f com.newreading.goodreels -l frida\auto-token-extractor.js
# Use app, then type: save()
# Ctrl+C to stop
adb pull /sdcard/goodshort_tokens.json .
```

#### Step 2: Capture Metadata

```bash
# Method 1: Use wrapper
production-pipeline.bat
# Select option 2

# Method 2: Manual
frida -U -f com.newreading.goodreels -l frida\production-scraper.js
# Browse dramas in app
# Type: status() to check progress
# Type: save() when done
# Ctrl+C to stop
adb pull /sdcard/goodshort_production_data.json .
```

#### Step 3: Process Data

```bash
# Method 1: Use wrapper
production-pipeline.bat
# Select option 3

# Method 2: Manual
python production_processor.py
```

---

## 📊 Using the Frida Scripts

### Token Extractor Commands

```javascript
status()  // Show extracted tokens
save()    // Force save to file
export()  // Print JSON to console
```

### Production Scraper Commands

```javascript
status()        // Show capture statistics
list()          // List all captured dramas
save()          // Force save to file
export()        // Export complete JSON
getDrama(id)    // Get specific drama data
```

---

## 📱 App Browsing Tips

To capture maximum data:

1. **Browse Popular Section**
   - Scroll through trending/popular dramas
   - Captures bulk metadata from list API

2. **Tap Drama Details**
   - Opens drama detail page
   - Captures full metadata (title, description, cover)

3. **Scroll Episode List**
   - View episode list
   - Captures chapter metadata

4. **Repeat for Multiple Dramas**
   - More dramas browsed = more data captured
   - Recommend: 10-20 dramas for good dataset

---

## 📂 Output Structure

```
production_output/
├── final_metadata.json       # Complete production metadata
├── database_import.sql       # SQL import script
└── covers/                   # Downloaded cover images
    ├── 31000908479.jpg
    ├── 31001250379.jpg
    └── 31000991502.jpg
```

### final_metadata.json Structure

```json
{
  "31000908479": {
    "bookId": "31000908479",
    "title": "Si Manis yang Tak Bisa Jauh",  // Real title!
    "description": "Full drama description...",
    "cover": "/api/covers/31000908479.jpg",
    "coverLocal": "C:\\...\\covers\\31000908479.jpg",
    "genre": "Romance",
    "category": "Drama Indonesia",
    "tags": ["Romance", "Modern Life"],
    "totalEpisodes": 80,
    "episodes": [
      {
        "episodeNumber": 1,
        "title": "Episode 1",
        "chapterId": "123456",
        "duration": 180,
        "videoUrl": "/api/videos/31000908479/episode-1.m3u8"
      }
    ],
    "productionMetadata": {
      "hasRealTitle": true,
      "hasRealCover": true,
      "isComplete": true
    }
  }
}
```

---

## 🔄 Token Auto-Refresh

The system automatically refreshes tokens:

1. **Auto-Extract**: Tokens captured during app usage
2. **Auto-Save**: Saved to `/sdcard/goodshort_tokens.json`
3. **Auto-Update**: New tokens override old ones
4. **Manual Force**: Type `save()` in Frida console

No manual token management needed!

---

## ✅ Validation

The processor automatically validates:
- ✅ Real title captured (not placeholder)
- ✅ Cover URL present
- ✅ Description available
- ✅ Episode list complete

Stats displayed after processing:
```
Total Dramas:       10
Complete Metadata:  8 ✅
Covers Downloaded:  10
Missing Titles:     2
Missing Covers:     0
```

---

## 🎬 Import to Database

### Option 1: SQL Script
```sql
-- Use generated SQL
psql -U postgres -d kingshortid -f production_output/database_import.sql
```

### Option 2: Custom Import
```javascript
// Read final_metadata.json
const metadata = require('./production_output/final_metadata.json');

// Import to your database
for (const [bookId, drama] of Object.entries(metadata)) {
  await db.drama.create({
    sourceId: drama.bookId,
    source: 'goodshort',
    title: drama.title,
    description: drama.description,
    cover: drama.cover,
    // ... rest of fields
  });
}
```

### Copy Covers
```bash
# Copy to backend public folder
cp production_output/covers/* d:\kingshortid\backend\public\covers\
```

---

## 🐛 Troubleshooting

### "Frida not found"
```bash
pip install frida-tools
```

### "No device found"
Start your Android emulator first

### "Data file not found"
```bash
# Pull manually
adb pull /sdcard/goodshort_production_data.json .
```

### "No metadata captured"
**Cause:** App using cached data

**Solution:**
1. Force close app
2. Clear app cache (not data!)
3. Restart Frida script
4. Browse **different** dramas

### "Covers not downloading"
**Cause:** Cover URLs not captured

**Solution:**
- Browse dramas that show big cover posters
- Tap drama details (triggers cover API)
- Check `status()` - should show covers found

---

## 📈 Production Checklist

- [ ] Tokens extracted successfully
- [ ] Browsed 10+ dramas in app
- [ ] `status()` shows captured dramas
- [ ] Data pulled from device
- [ ] Processor runs without errors
- [ ] Covers downloaded to local folder
- [ ] `final_metadata.json` generated
- [ ] Metadata validation passes
- [ ] Covers exist for all dramas
- [ ] Ready to import to database! 🚀

---

## 🎯 Benefits Over Previous Approach

| Feature | Old System | New System |
|---------|-----------|------------|
| Title | Generic placeholders | ✅ Real drama titles |
| Cover | Screenshot/generic | ✅ Real CDN covers |
| Automation | Manual steps | ✅ Fully automated |
| Token Refresh | Manual | ✅ Auto-refresh |
| Data Quality | Incomplete | ✅ Complete metadata |
| Save | Manual copy | ✅ Auto-save |
| Import | Manual | ✅ SQL script generated |

---

## 💡 Tips for Best Results

1. **First Run**: Extract tokens first
2. **Browse Variety**: Different genres, categories
3. **Be Patient**: Let API responses load
4. **Check Progress**: Use `status()` frequently
5. **Save Often**: Type `save()` every 5-10 dramas
6. **Complete Dataset**: Browse 15-20 dramas minimum

---

## 🚀 Ready to Deploy!

After processing, you'll have:
- ✅ **Real titles** from GoodShort
- ✅ **Real covers** downloaded locally
- ✅ **Complete metadata** (description, genre, episodes)
- ✅ **Database import script** ready
- ✅ **Production-ready** JSON

**No more placeholders. No more manual work. Professional quality!** 🎬

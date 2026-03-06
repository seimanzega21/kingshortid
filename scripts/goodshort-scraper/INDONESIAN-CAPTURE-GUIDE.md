# Capturing Indonesian Drama Metadata - Quick Guide

## 🎯 Your Goal
Capture **5-10 Indonesian dramas** with:
- ✅ **Indonesian titles** (not Chinese/English)
- ✅ **Full metadata** (description, author, category)
- ✅ **Cover images**
- ✅ **10-15 episodes per drama**

---

## 🚀 How to Start

### Step 1: Launch Metadata Capture Script

**Option A: Double-Click (Easiest)**
```
Double-click: start-capture-metadata.bat
```

**Option B: Command Line**
```bash
cd d:\kingshortid\scripts\goodshort-scraper
frida -U -f com.newreading.goodreels -l frida\capture-metadata.js
```

### Step 2: Browse Indonesian Dramas

**In GoodShort app:**
1. **Look for dramas with Indonesian titles:**
   - "Kembalnya Sang Legenda"
   - "Bangkit Demi Anakku"
   - "Cinta Di Era 80-an"
   - "Kumiskinkan Mantan Suamiku"
   - etc.

2. **Tap each drama** to open detail page
   - Script will capture: Title, Description, Cover
   - You'll see: `📖 [METADATA CAPTURED] {Title}`

3. **Browse 10-15 episodes** per drama
   - Just tap each episode → wait 2 seconds → back → next episode
   - You'll see: `📺 Episode X captured`

4. **Repeat for 5-10 dramas**

---

## 📊 Monitor Progress

### Check Status Anytime
Type in Frida console:
```javascript
status()
```

Expected output after 1 hour:
```
┌─────────────────────────────────────────────────────────┐
│  📊 CAPTURE STATUS                                      │
├─────────────────────────────────────────────────────────┤
│  Dramas: 5         Episodes: 60                         │
│  With Metadata: 5                                       │
└─────────────────────────────────────────────────────────┘
```

### List Captured Dramas
```javascript
list()
```

Shows all dramas with titles and metadata status.

---

## 💾 Export Data When Done

### Step 1: Export JSON
In Frida console:
```javascript
exportData()
```

### Step 2: Copy JSON
- Select all JSON output (from `{` to `}`)
- Copy (Ctrl+C)

### Step 3: Save to File
1. Open: `d:\kingshortid\scripts\goodshort-scraper\captured-episodes.json`
2. **Replace entire content** with the copied JSON
3. Save (Ctrl+S)

---

## ✅ What Makes Good Metadata?

Script will capture:
```json
{
  "metadata": {
    "title": "Kumiskinkan Mantan Suamiku",  // ✅ Indonesian title
    "description": "Setelah bercerai...",   // ✅ Indonesian description
    "cover": "https://acf.goodreels.com/...",// ✅ Cover URL
    "author": "Penulis ABC",
    "totalChapters": 80,
    "category": "Reinkarnasi",
    "language": "id"                         // ✅ Indonesian
  }
}
```

---

## 🎬 After Capture Complete

### 1. Download Videos
```bash
npm run download
```
- Downloads all captured episodes
- Merges `.ts` segments into MP4 files
- Saves to `downloads/` folder

### 2. Upload to R2
```bash
npx ts-node src/upload-to-r2.ts
```
- Uploads all MP4 videos to Cloudflare R2
- Uploads cover images
- Generates R2 URLs

### 3. Import to Database
```bash
npx ts-node src/import-goodshort.ts
```
- Imports dramas with **Indonesian titles** from metadata
- Imports episodes with R2 video URLs
- Updates Railway PostgreSQL database

### 4. Test in Mobile App
- Open KingShortID app
- Browse dramas - should see **Indonesian titles**
- Play videos - should load from R2

---

## 🔍 How to Identify Indonesian Dramas?

**Look for keywords in titles:**
- Contains Indonesian words: "Kembalnya", "Bangkit", "Cinta", "Kumiskinkan"
- Reinkarnasi/Romance themes common in Indonesian short dramas
- **Avoid**: Chinese characters, pure English titles

**Categories to target:**
- Reinkarnasi (Reincarnation)
- Balas Dendam (Revenge)
- Manis (Sweet Romance)
- Identitas Tersembunyi (Hidden Identity)

---

## ⚡ Pro Tips

1. **Focus on complete dramas** - avoid ongoing series
2. **Check episode count** - aim for dramas with 60-100 episodes
3. **Verify language** - tap into episode to see if subtitles/UI are Indonesian
4. **Quality over quantity** - 5 complete dramas better than 10 incomplete
5. **Monitor metadata** - make sure you see `📖 [METADATA CAPTURED]` for each drama

---

## 🎯 Success Criteria

You're ready to proceed when:
- ✅ Captured 5-10 dramas
- ✅ All dramas have Indonesian titles
- ✅ Each drama has 10+ episodes
- ✅ Metadata shows status: "With Metadata: 5+"
- ✅ JSON exported and saved

---

**Any questions? Start capture and browse the app!** 🚀

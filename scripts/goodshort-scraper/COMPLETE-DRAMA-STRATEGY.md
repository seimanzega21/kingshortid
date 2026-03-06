# Complete Drama Capture Strategy - Indonesian Focus

## 🎯 Strategy: One Complete Drama at a Time

**Goal:** Capture **FULL dramas** with ALL episodes, one drama at a time.

**Example:**
- ✅ Drama 1: 78/78 episodes (COMPLETE)
- ✅ Drama 2: 65/65 episodes (COMPLETE)
- ❌ ~~Drama 1: 15/78 episodes (INCOMPLETE)~~

---

## 📱 Step-by-Step Capture

### Step 1: Launch Capture Script

```bash
cd d:\kingshortid\scripts\goodshort-scraper
start-capture-metadata.bat
```

You'll see:
```
[✓] Hooking complete!
📱 Now browse dramas in the app
```

---

### Step 2: Pick ONE Indonesian Drama

**Look for complete dramas with Indonesian titles:**

**Recommended categories:**
- **Reinkarnasi** (60-100 episodes typically)
- **Balas Dendam** (60-80 episodes)
- **Identitas Tersembunyi** (70-90 episodes)

**Good examples:**
- "Kembalikan Aku yang Dulu" (78 eps)
- "Bangkit Demi Anakku" (85 eps)
- "Kumiskinkan Mantan Suamiku" (92 eps)
- "CEO Misterius Suamiku" (68 eps)

**Check episode count BEFORE starting:**
- Tap drama → Check "Total Episodes: 78"
- Make sure status = "Selesai" (Completed)

---

### Step 3: Capture Drama Metadata

1. **Tap the drama** → Detail page opens
2. Wait 2 seconds
3. Frida console shows:
   ```
   🎬 [NEW DRAMA] Book ID: 31000908479
   📖 [METADATA CAPTURED] Kembalikan Aku yang Dulu
      Book ID: 31000908479
      Desc: Setelah bercerai dengan suami yang...
   ```

✅ **Metadata captured!** Now capture all episodes...

---

### Step 4: Speed-Capture ALL Episodes

**Fast tap method:**
1. **Tap Episode 1** → Wait 2-3 seconds (video URL loads)
2. **Back** ← 
3. **Tap Episode 2** → Wait 2-3 seconds
4. **Back** ←
5. **Repeat** for Episode 3, 4, 5... until the last episode

**You'll see in Frida console:**
```
   📺 Episode 1 captured (Chapter: 411618)
   📺 Episode 2 captured (Chapter: 411619)
   📺 Episode 3 captured (Chapter: 411620)
   ...
   📺 Episode 78 captured (Chapter: 411695)

┌─────────────────────────────────────────────────────────┐
│  📊 CAPTURE STATUS                                      │
├─────────────────────────────────────────────────────────┤
│  Dramas: 1         Episodes: 78                         │
│  With Metadata: 1                                       │
└─────────────────────────────────────────────────────────┘
```

---

### Step 5: Verify Complete

In Frida console:
```javascript
list()
```

Should show:
```
1. Kembalikan Aku yang Dulu
   ID: 31000908479 | Episodes: 78 | Metadata: ✓
   Setelah bercerai dengan suami yang kejam...
```

**If all 78 episodes captured:** ✅ Drama 1 COMPLETE!

---

### Step 6: Move to Next Drama (Optional)

If you want more dramas, repeat Step 2-5 for Drama 2, Drama 3, etc.

**Target for first session:**
- **Minimum:** 1 complete drama (60-100 episodes)
- **Ideal:** 2-3 complete dramas (180-250 episodes total)
- **Maximum:** 5 complete dramas (400-500 episodes)

---

### Step 7: Export Data

When done capturing, in Frida console:

```javascript
exportData()
```

**Copy the entire JSON output**

Open:
```
d:\kingshortid\scripts\goodshort-scraper\captured-episodes.json
```

**Paste and save** the JSON.

---

## ⚡ Speed Tips

### Fast Episode Capture
- **Don't wait for video to play** - just 2-3 seconds for URL load
- **Use fast taps:** Tap → Back → Tap → Back
- **Rhythm:** ~5 episodes per minute
- **78 episodes ≈ 15-20 minutes**

### Break Strategy
- **After 20-30 episodes:** Take 1 minute break
- **Check progress:** `status()` in console
- **Resume:** Continue from last episode

### Multi-Session
If app crashes or you need to pause:
- **exportData()** → Save progress
- **Restart Frida** later
- **Continue** from where you left off (Frida merges data)

---

## 📊 Time Estimates

| Drama Size | Capture Time | Download Time | Total |
|------------|--------------|---------------|-------|
| 60 eps     | ~12-15 min   | ~30-45 min    | ~1 hour |
| 80 eps     | ~15-20 min   | ~40-60 min    | ~1.5 hours |
| 100 eps    | ~20-25 min   | ~50-75 min    | ~2 hours |

**For 3 complete dramas (240 episodes):** ~4-5 hours total

---

## ✅ Quality Checklist

Before exporting, verify:
- ✅ All episodes captured (e.g., 78/78, not 75/78)
- ✅ Metadata includes Indonesian title
- ✅ Cover image captured
- ✅ No gaps in episode numbers

**Check in Frida console:**
```javascript
status()  // Should show "With Metadata: 1" or higher
list()    // Verify episode count matches drama's total
```

---

## 🎯 Recommended First Drama

**Search for:** "Reinkarnasi" category in GoodShort

**Look for:**
- ✅ Completed status (Selesai)
- ✅ Indonesian title
- ✅ 60-100 episodes
- ✅ High rating/views (quality content)

**Example perfect dramas:**
1. "Kembalikan Aku yang Dulu" (78 eps, Reinkarnasi)
2. "CEO Dingin Jatuh Cinta" (85 eps, Romance)
3. "Balas Dendam Istriku" (72 eps, Balas Dendam)

---

## 📝 After Capture Complete

Once you have 1+ complete drama:

```bash
# Step 1: Download all episodes (540p + 720p)
npm run download

# Step 2: Upload to R2
npm run upload

# Step 3: Import to database
npm run import

# Step 4: Test in KingShortID mobile app
```

---

**Ready? Start with ONE complete Indonesian drama! 🚀**

**Tip:** Pick a drama YOU would actually watch - quality matters! 😊

# Full Scraping Session - Strategy Guide

## Goal
Capture **5-10 dramas** dengan **10-15 episode each** = **50-150 total episodes**

---

## Efficient Capture Strategy

### Method: "Speed Tap" Technique

1. **Pilih Drama** dari home screen
2. **Masuk ke Episode List** 
3. **Rapid Tap Episodes:**
   - Tap Episode 1 → tunggu 2 detik (video start loading)
   - **Back** ke episode list
   - Tap Episode 2 → tunggu 2 detik
   - Back
   - Tap Episode 3... dst
   - **Ulangi sampai episode 10-15**

4. **Back to Home** → pilih drama baru
5. **Ulangi** untuk 5-10 drama

### Why This Works
- Frida capture URL **saat request dibuat**, bukan saat video selesai load
- Cukup tunggu **video mulai buffer** (2-3 detik)
- **Tidak perlu** nonton full video
- **10x lebih cepat** dari nonton

---

## Recommended Dramas (From Screenshot)

Pilih dari list ini:
1. ✅ Kembalnya Sang Legenda (Perangi Bients)
2. ✅ Bangkit Demi Anakku (Reinkarnasi)
3. Cinta Di Era 80-an (Reinkarnasi)
4. Ciumlah Aku (Manis)
5. Hidupku Hanya Untukmu (Manis)
6. Kumiskinkan Mantan Suamiku (Reinkarnasi)
7. Salah Kenal, Cinta Tumbuh (Manis)
8. Takkan Kumaafkan (Identitas Tersembunyi)

**Target:** 5 drama × 12 episode = **60 episodes**

---

## Monitor Progress

### Di Frida Terminal
Setiap episode captured akan muncul:
```
📺 Episode X captured (Chapter: xxxxx)
```

### Check Status Kapan Saja
Ketik di Frida console:
```javascript
status()
```

Expected output setelah 1 jam scraping:
```
┌─────────────────────────────────────────┐
│  Dramas: 5      Episodes: 60            │
└─────────────────────────────────────────┘
```

---

## Timeline Estimate

| Task | Time | Description |
|------|------|-------------|
| Capture 5 dramas | 30-60 min | Speed tap 10-15 episode per drama |
| Export data | 1 min | `exportData()` dan copy JSON |
| Download videos | 30-60 min | Automated batch download |
| **Total** | **1-2 hours** | Ready for R2 upload |

---

## After Capture Complete

1. **Export Data:**
   ```javascript
   status()      // Verify count
   exportData()  // Get JSON
   ```

2. **Save JSON:**
   - Copy output
   - Save to `captured-episodes.json`

3. **Batch Download:**
   ```bash
   npm run download
   ```

4. **Wait for R2 Bucket** dari user

5. **Upload & Import:**
   ```bash
   npm run upload    # Upload ke R2
   npm run import    # Import to database
   ```

---

## Tips

- **Focus on complete dramas** (yang punya banyak episode)
- **Vary genres** untuk content diversity
- **Check capture** setiap 5-10 episode dengan `status()`
- **Jangan rush** - better 5 complete dramas than 10 incomplete

---

## Current Status

**Frida:** ✅ Running  
**App:** ✅ GoodShort opened  
**Ready to capture!** 🎬

**Mulai browse sekarang!**

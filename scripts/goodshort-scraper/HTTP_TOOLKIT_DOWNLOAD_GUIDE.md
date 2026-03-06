# HTTP Toolkit - Video Download Test Guide

## 🎯 Objective
Extract headers dari HTTP Toolkit dan test download video segment dengan authentication yang benar.

---

## 📋 Step-by-Step Instructions

### Step 1: Pastikan HTTP Toolkit Connected

1. **Buka HTTP Toolkit**
2. **Status harus HIJAU** (connected to emulator)
3. **Clear existing requests** (optional - biar bersih)

---

### Step 2: Play Video di Emulator

1. **Buka GoodShort app** di emulator
2. **Tap drama apa saja**
3. **Play 1 episode** - tunggu 10-15 detik sampai buffering
4. **Biarkan video jalan** (jangan pause)

---

### Step 3: Cari Request .ts yang SUKSES

Di HTTP Toolkit:

1. **Filter by:** `video` atau search `.ts`
2. **Cari yang status:** `200 OK` (PENTING!)
3. **Harus:** file berakhiran `.ts` (bukan `.m3u8`)
4. **Contoh URL:**
   ```
   https://v2-akm.goodreels.com/mts/books/.../segment_000000.ts
   ```

---

### Step 4: Copy as cURL

1. **Klik kanan** pada request .ts yang 200 OK
2. **Pilih:** "Copy as cURL" atau "Export → cURL"
3. **Paste** ke notepad/text editor

**Expected result:**
```bash
curl 'https://v2-akm.goodreels.com/mts/books/502/31000991502/469570/pkck6km31v/720p/8r5aonu6g0_720p_000000.ts' \
  -H 'authority: v2-akm.goodreels.com' \
  -H 'accept: */*' \
  -H 'user-agent: Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86 Build/RSR1.201013.001)' \
  -H 'referer: https://api-akm.goodreels.com/' \
  -H 'accept-encoding: gzip, deflate, br' \
  --compressed
```

---

### Step 5: Save cURL Command

**Simpan ke file:**
```
d:\kingshortid\scripts\goodshort-scraper\curl_export.txt
```

**PENTING:** Paste FULL cURL command (termasuk semua `-H` headers!)

---

### Step 6: Run Header Extraction

```bash
cd d:\kingshortid\scripts\goodshort-scraper
python download_with_http_toolkit.py --parse-curl curl_export.txt
```

**Expected output:**
```
✅ Headers saved to: http_toolkit_headers.json

📋 Extracted headers:
  authority: v2-akm.goodreels.com
  user-agent: Dalvik/2.1.0...
  referer: https://api-akm.goodreels.com/
```

---

### Step 7: Test Single Segment Download

```bash
# Test download 1 segment
python download_with_http_toolkit.py --test-url "URL_DARI_CURL"
```

**Expected:** File `test_segment.ts` ter-download (size > 0 bytes)

---

## ✅ Verification Checklist

- [ ] HTTP Toolkit connected (hijau)
- [ ] Video played & buffering
- [ ] Found .ts request with 200 OK
- [ ] Copied FULL cURL (with all headers)
- [ ] Saved to curl_export.txt
- [ ] Headers extracted successfully
- [ ] Test download works

---

## 🐛 Troubleshooting

### "No .ts requests found"
- Play video lebih lama (30+ seconds)
- Check filter: remove filters, show all requests

### "All requests are 403"
- Video belum buffering
- Restart app & HTTP Toolkit connection

### "cURL command too short"
- Make sure you copied FULL command
- Should have multiple `-H` lines

---

## 🎯 Next After Success

Once headers extracted:
```bash
# Download full episode
python download_with_http_toolkit.py --drama-folder test_output\jenderal_jadi_tukang
```

This will:
1. Parse HLS playlist
2. Download ALL .ts segments
3. Combine to video.mp4

---

## 📞 Ready to Test?

Sekarang:
1. ✅ Buka HTTP Toolkit (pastikan connected)
2. ✅ Play video di emulator
3. ✅ Copy cURL dari request .ts
4. ✅ Report hasil di sini!

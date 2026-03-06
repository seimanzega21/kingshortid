# GoodShort HLS URL Pattern Analysis

## Captured HLS URLs

### Episode 1 Example:
```
https://v2-akm.goodreels.com/mts/books/963/31001221963/614590/t5hgdagimt/720p/viisdqecsr_720p.m3u8
```

## URL Structure Breakdown

```
https://v2-akm.goodreels.com/mts/books/{last3}/{bookId}/{episodeId}/{hash1}/720p/{hash2}_720p.m3u8
                                         ^^^   ^^^^^^^^^ ^^^^^^^^^  ^^^^^^^^       ^^^^^^^^^^
                                         963   31001221963  614590   t5hgdagimt    viisdqecsr
```

### Components:
1. **CDN Base**: `v2-akm.goodreels.com`
2. **Path**: `/mts/books/`
3. **Last 3 Digits**: `963` (from bookId: 310012219**63**)
4. **Book ID**: `31001221963`
5. **Episode ID**: `614590`
6. **Hash 1**: `t5hgdagimt` (10 chars, lowercase alphanumeric)
7. **Hash 2**: `viisdqecsr` (10 chars, lowercase alphanumeric)
8. **Quality**: `720p`

## Pattern Questions

### ❓ Are hashes static or dynamic?
- **Need to test**: Play same episode multiple times
- Check if hash changes per session/time

### ❓ Is there authentication?
- Try direct curl/wget without headers
- Check if need cookies/tokens

### ❓ Segment URL pattern?
- M3U8 contains: relative paths or absolute?
- Segments named: `{hash}_*.ts` or numbered?

## Testing Strategy

### Test 1: Direct m3u8 Access
```bash
curl "https://v2-akm.goodreels.com/mts/books/963/31001221963/614590/t5hgdagimt/720p/viisdqecsr_720p.m3u8"
```

**Expected**:
- ✅ Works → No auth needed, can download directly
- ❌ 403/401 → Need headers/tokens
- ❌ Error page → CDN blocked, need user-agent

### Test 2: Parse M3U8 for segment pattern
```python
import requests
response = requests.get(url, headers={'User-Agent': 'GoodShort/2.5.1'})
playlist = response.text
# Extract segment URLs
```

### Test 3: Download segments
```python
# If segments are relative paths:
base_url = "https://v2-akm.goodreels.com/mts/books/963/31001221963/614590/t5hgdagimt/720p/"
segments = parse_m3u8(playlist)
for segment in segments:
    download(base_url + segment)
```

## Next Steps

1. ✅ **Test direct m3u8 access** (различные headers)
2. ✅ **Parse m3u8 playlist** structure  
3. ✅ **Download test segments**
4. ⚠️ **Reverse engineer hash generation** (if needed)
5. ✅ **Build complete downloader**

## Hash Generation Theories

### Theory 1: Random per session
- New hash each time episode is loaded
- Need to capture from app

### Theory 2: Derived from episode data
- Hash = f(bookId, episodeId, timestamp)
- Can reverse engineer

### Theory 3: Static per episode
- Same hash always
- Easy! Just store mapping

## Tools Needed

1. **mitmproxy** or **HTTP Toolkit**
   - Intercept HTTPS traffic from GoodShort app
   - Capture complete request headers
   - See if hash changes

2. **Python requests**
   - Test direct downloads
   - Parse m3u8 playlists

3. **m3u8 parser library**
   ```bash
   pip install m3u8
   ```

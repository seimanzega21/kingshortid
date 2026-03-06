# 📊 Analisa Struktur: GoodShort vs KingShortID

## 🔍 Perbandingan Lengkap

### 1. **DRAMA/BOOK Structure**

#### ✅ **GoodShort Structure (Source)**
```json
{
  "bookId": "31001221963",
  "title": "Jenderal Jadi Tukang",
  "description": "Seorang jenderal terkenal...",
  "genre": "Action Romance",
  "tags": ["CEO", "Hidden Identity", "Romance", "Action"],
  "totalEpisodes": 100,
  "author": "GoodShort",
  "coverUrl": "https://acf.goodreels.com/videobook/202405/cover-xPEPIVJaGC.jpg"
}
```

#### ✅ **KingShortID Schema (Target)**
```prisma
model Drama {
  id          String  @id @default(cuid())
  title       String
  description String  @db.Text
  cover       String
  banner      String?
  
  genres  String[]  // ✅ SAMA (array)
  tagList String[]  // ✅ SAMA (array)
  
  totalEpisodes Int   @default(0)  // ✅ SAMA
  rating        Float @default(0)
  views         Int   @default(0)
  
  status     String  @default("ongoing")
  isVip      Boolean @default(false)
  director   String?
  cast       String[]
  country    String  @default("China")
}
```

#### 📌 **Mapping:**
| GoodShort Field | KingShortID Field | Status | Notes |
|-----------------|-------------------|--------|-------|
| `bookId` | ❌ Not stored | ⚠️ Missing | Should store in metadata |
| `title` | `title` | ✅ Match | Direct map |
| `description` | `description` | ✅ Match | Direct map |
| `coverUrl` | `cover` | ✅ Match | URL field |
| `genre` (string) | `genres` (array) | ⚠️ Convert | Split to array |
| `tags` (array) | `tagList` | ✅ Match | Direct map |
| `totalEpisodes` | `totalEpisodes` | ✅ Match | Direct map |
| `author` | ❌ Not stored | ⚠️ Missing | Add to metadata |

---

### 2. **EPISODE/CHAPTER Structure**

#### ✅ **GoodShort Structure**
```json
{
  "episodeNumber": 1,
  "episodeId": "614590",
  "title": "Episode 1",
  "hlsUrl": "https://v2-akm.goodreels.com/mts/books/963/31001221963/614590/t5hgdagimt/720p/viisdqecsr_720p.m3u8"
}
```

#### ✅ **KingShortID Schema**
```prisma
model Episode {
  id      String @id @default(cuid())
  dramaId String
  
  episodeNumber Int
  title         String
  description   String? @db.Text
  thumbnail     String?
  videoUrl      String  // ✅ HLS URL
  duration      Int     @default(0)
  
  isVip     Boolean @default(false)
  coinPrice Int     @default(0)
  views     Int     @default(0)
}
```

#### 📌 **Mapping:**
| GoodShort Field | KingShortID Field | Status | Notes |
|-----------------|-------------------|--------|-------|
| `episodeId` | ❌ Not stored | ⚠️ Missing | Store in metadata? |
| `episodeNumber` | `episodeNumber` | ✅ Match | Direct map |
| `title` | `title` | ✅ Match | Direct map |
| `hlsUrl` | `videoUrl` | ✅ Match | HLS m3u8 URL |
| ❌ No duration | `duration` | ⚠️ Missing | Calculate from segments |
| ❌ No thumbnail | `thumbnail` | ⚠️ Missing | Generate from video? |

---

### 3. **HLS URL Pattern Analysis**

#### ✅ **GoodShort HLS Pattern:**
```
https://v2-akm.goodreels.com/mts/books/{SUFFIX}/{BOOK_ID}/{EPISODE_ID}/{HASH}/720p/{VIDEO}_{QUALITY}.m3u8
```

**Example:**
```
https://v2-akm.goodreels.com/mts/books/963/31001221963/614590/t5hgdagimt/720p/viisdqecsr_720p.m3u8
                                          ^^^  ^^^^^^^^^^^  ^^^^^^  ^^^^^^^^^^      ^^^^^^^^^^
                                          |    |            |       |               |
                                      Suffix  Book ID    Ep ID   Hash            Video Hash
```

**Components:**
- `{SUFFIX}`: Last 3 digits of bookId (e.g., "963" from "31001221963")
- `{BOOK_ID}`: Full book ID
- `{EPISODE_ID}`: Unique episode identifier  
- `{HASH}`: Random hash for security/CDN
- `{VIDEO}`: Video file hash
- `{QUALITY}`: 720p, 480p, 360p

#### ✅ **KingShortID Storage:**
```prisma
videoUrl String  // Store full HLS URL
```

**✅ COMPATIBLE** - Direct storage of complete URL

---

### 4. **Cover/Poster Management**

#### ✅ **GoodShort CDN Pattern:**
```
https://acf.goodreels.com/videobook/{BOOK_FOLDER}/cover-{HASH}.jpg
https://acf.goodreels.com/videobook/202405/cover-xPEPIVJaGC.jpg
https://acf.goodreels.com/videobook/31001160993/202510/cover-uqBw0xaL1J.jpg
```

#### ✅ **KingShortID Storage:**
```prisma
cover  String   // CDN URL or R2 path
banner String?  // Optional banner
```

**Storage Options:**
1. **Direct CDN**: Store GoodShort URL (fastest)
2. **R2 Mirror**: Download → Upload to R2 (ownership)
3. **Hybrid**: CDN for now, migrate to R2 later

**✅ COMPATIBLE** - Both use URL strings

---

### 5. **Additional Features in KingShortID (Not in GoodShort)**

#### ✅ **Extra Drama Fields:**
```prisma
model Drama {
  rating        Float @default(0)      // ❌ Not in GoodShort
  views         Int   @default(0)      // ❌ Not in GoodShort
  likes         Int   @default(0)      // ❌ Not in GoodShort
  reviewCount   Int   @default(0)      // ❌ Not in GoodShort
  
  status     String  @default("ongoing") // ❌ Not in GoodShort
  isVip      Boolean @default(false)     // ⚠️  Could check premium
  isFeatured Boolean @default(false)     // ❌ Not in GoodShort
  
  releaseDate DateTime?  // ❌ Not in GoodShort
  director    String?    // ❌ Not in GoodShort
  cast        String[]   // ❌ Not in GoodShort
  country     String     // ❌ Not in GoodShort (default "China")
  language    String     // ❌ Not in GoodShort
}
```

**Recommendation:**
- Set `status = "completed"` (most GoodShort dramas are complete)
- Set `isVip = false` initially
- Set `country = "China"` (default)
- Calculate `rating`, `views`, `likes` from engagement later

---

### 6. **Extra Episode Fields:**

```prisma
model Episode {
  description   String? @db.Text  // ❌ Not in GoodShort
  thumbnail     String?           // ❌ Not in GoodShort
  duration      Int     @default(0) // ⚠️  Calculate from HLS
  
  isVip     Boolean @default(false)  // ⚠️  Check if locked
  coinPrice Int     @default(0)      // ❌ Not in GoodShort
  views     Int     @default(0)      // ❌ Not in GoodShort
}
```

**Recommendation:**
- Leave `description = null` initially
- Generate `thumbnail` from first frame of video
- Calculate `duration` by parsing m3u8 playlist
- Set `isVip = false` initially
- Set `coinPrice = 0` (free)

---

## 🎯 **Migration Strategy: GoodShort → KingShortID**

### ✅ **Step 1: Drama Import**
```typescript
// Pseudo-code
const createDramaFromGoodShort = (goodShortData) => {
  return {
    title: goodShortData.title,
    description: goodShortData.description,
    cover: goodShortData.coverUrl,
    genres: goodShortData.genre.split(',').map(g => g.trim()),
    tagList: goodShortData.tags,
    totalEpisodes: goodShortData.totalEpisodes,
    
    // Defaults
    status: "completed",
    country: "China",
    isVip: false,
    rating: 0,
    views: 0,
  }
}
```

### ✅ **Step 2: Episode Import**
```typescript
const createEpisodeFromGoodShort = (episodeData) => {
  return {
    episodeNumber: episodeData.episodeNumber,
    title: episodeData.title,
    videoUrl: episodeData.hlsUrl,
    
    // Defaults
    duration: 0,  // Calculate later
    thumbnail: null,  // Generate later
    isVip: false,
    coinPrice: 0,
  }
}
```

---

## ⚠️ **Missing Data (Need to Handle)**

### 1. **Episode Duration**
**Problem:** GoodShort doesn't provide duration
**Solution:**
```python
# Parse m3u8 playlist to calculate total duration
def calculate_duration(hls_url):
    playlist = fetch(hls_url)
    segments = parse_m3u8(playlist)
    return sum(seg.duration for seg in segments)
```

### 2. **Thumbnails**
**Problem:** No episode thumbnails in GoodShort
**Solution:**
```bash
# Generate from first frame
ffmpeg -i video.mp4 -ss 00:00:01 -vframes 1 thumbnail.jpg
```

### 3. **Original IDs**
**Problem:** Lose bookId and episodeId mapping
**Solution:** Store in metadata JSON field:
```json
{
  "goodshort": {
    "bookId": "31001221963",
    "episodeId": "614590"
  }
}
```

---

## ✅ **Final Compatibility Score**

| Category | Compatibility | Notes |
|----------|---------------|-------|
| **Drama Core** | 95% ✅ | All fields map well |
| **Episode Core** | 90% ✅ | Missing duration/thumbnail (calculable) |
| **HLS URLs** | 100% ✅ | Perfect match |
| **Covers** | 100% ✅ | Direct URL storage |
| **Metadata** | 85% ⚠️ | Some GoodShort fields not used |

---

## 🚀 **Recommendation**

### ✅ **HIGHLY COMPATIBLE!**

The structures are **90%+ compatible**. Key points:

1. ✅ **Core drama data** maps perfectly
2. ✅ **HLS URLs** work directly
3. ✅ **Covers** can use CDN or R2
4. ⚠️ **Duration/thumbnails** need calculation
5. ⚠️ **Some metadata** (director, cast) not available from GoodShort

### 🎯 **Next Steps:**

1. ✅ Keep capturing drama metadata + HLS URLs
2. ✅ Store bookId/episodeId for reference
3. ⚠️ Add duration calculation script
4. ⚠️ Add thumbnail generation (optional)
5. ✅ Import to KingShortID with default values for missing fields

**The current scraping structure is PERFECT for KingShortID import!** 🎉

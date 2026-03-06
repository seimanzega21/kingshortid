# Manual Metadata Entry for GoodShort Dramas

## Drama 1: 31001045572

**Fill in the following:**

```json
{
  "bookId": "31001045572",
  "title": "PUT_TITLE_HERE",
  "cover": "PUT_COVER_URL_HERE",
  "description": "PUT_DESCRIPTION_HERE",
  "author": "Unknown",
  "category": "Drama",
  "tags": [],
  "total_episodes": 16
}
```

**Instructions:**
1. Open GoodShort app
2. Find this drama (16 episodes)
3. Take screenshot of:
   - Drama title
   - Cover image
   - Description/synopsis
4. Fill in above JSON

---

## Drama 2: 31001070612

**Fill in the following:**

```json
{
  "bookId": "31001070612",
  "title": "PUT_TITLE_HERE",
  "cover": "PUT_COVER_URL_HERE",
  "description": "PUT_DESCRIPTION_HERE",
  "author": "Unknown",
  "category": "Drama",
  "tags": [],
  "total_episodes": 9
}
```

**Instructions:**
1. Open GoodShort app
2. Find this drama (9 episodes)
3. Take screenshot of:
   - Drama title
   - Cover image
   - Description/synopsis
4. Fill in above JSON

---

## How to Get Cover URL

### Method 1: From HTTP Toolkit
1. Open HTTP Toolkit
2. Clear previous captures
3. Browse to drama detail page
4. Look for image requests (*.jpg, *.png)
5. Copy URL

### Method 2: Screenshot Upload
1. Take screenshot of cover
2. Upload to imgur.com or similar
3. Use that URL

---

## Save Instructions

After filling both JSONs:

1. Save as `manual_metadata.json` in this format:

```json
{
  "31001045572": {
    "book Id": "31001045572",
    "title": "Your Title Here",
    "cover": "https://...",
    "description": "Your description...",
    "author": "Unknown",
    "category": "Drama",
    "tags": [],
    "total_episodes": 16
  },
  "31001070612": {
    "bookId": "31001070612",
    "title": "Your Title Here",
    "cover": "https://...",
    "description": "Your description...",
    "author": "Unknown",
    "category": "Drama",
    "tags": [],
    "total_episodes": 9
  }
}
```

2. Run: `python apply_manual_metadata.py`

This will update the metadata.json files in r2_ready folders!

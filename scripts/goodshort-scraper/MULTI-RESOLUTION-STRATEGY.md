# Multi-Resolution Video Handling Strategy

## Current Situation
Episode model has single `videoUrl` field:
```prisma
model Episode {
  videoUrl String  // Single URL field
}
```

## Solution Options

### Option 1: Use videoUrl for 720p, Add Custom Field Later ✅ (RECOMMENDED)
**For now:**
- Store **720p** URL in `videoUrl` (default quality)
- Store **540p** URL in `description` field temporarily (as JSON metadata)
- Mobile app uses 720p by default

**Later (when ready):**
- Add migration to add `videoUrl540p` field
- Move 540p URLs from description to new field
- Add quality selector UI in mobile app

**Pros:**
- No schema change needed now
- Works immediately
- Can upgrade cleanly later

### Option 2: JSON in Single Field
Store both URLs as JSON in `videoUrl`:
```json
{
  "540p": "https://r2.dev/...540p.mp4",
  "720p": "https://r2.dev/...720p.mp4"
}
```

**Pros:**
- Single field, flexible
- Easy to add more resolutions

**Cons:**
- Mobile app needs to parse JSON
- Not standard URL field

### Option 3: Add Schema Fields Now
Add these fields to Episode model:
```prisma
model Episode {
  videoUrl      String  // 720p (default)
  videoUrl540p  String? // Optional 540p
}
```

**Pros:**
- Clean, proper structure
- Type-safe

**Cons:**
- Requires Prisma migration
- Need to coordinate with backend deployment

---

## Recommended Implementation (Option 1 for Now)

### R2 Upload
Upload both resolutions to R2 with naming:
```
goodshort-content/
└── {bookId}/
    ├── {chapterId}_540p.mp4
    ├── {chapterId}_720p.mp4
    └── cover.jpg
```

### Database Import (Current)
```typescript
{
  videoUrl: "https://r2.dev/.../31000908479/411618_720p.mp4", // Default 720p
  description: JSON.stringify({
    videoUrl540p: "https://r2.dev/.../31000908479/411618_540p.mp4",
    originalDescription: "Episode description here..."
  })
}
```

### Mobile App (Current)
- Uses `videoUrl` (720p) by default
- Ignores description metadata for now

### Future Upgrade Path
When ready to add quality selector:

1. **Backend Migration:**
   ```prisma
   model Episode {
     videoUrl      String
     videoUrl540p  String?
     videoUrl360p  String?  // Future
   }
   ```

2. **Data Migration Script:**
   ```sql
   UPDATE "Episode"
   SET "videoUrl540p" = (description::json->>'videoUrl540p')
   WHERE description LIKE '%videoUrl540p%';
   ```

3. **Mobile App Update:**
   - Add quality selector UI
   - Switch between videoUrl (720p) and videoUrl540p

---

## Current Implementation

For this scraping session, I'll use **Option 1**:
- ✅ Download 540p + 720p
- ✅ Upload both to R2
- ✅ Save 720p in `videoUrl`
- ✅ Save 540p reference in separate JSON file
- ✅ Mobile app uses 720p (smooth, no changes needed)
- ⏭️  Quality selector = wait for user request

This gives maximum flexibility without blocking current progress!

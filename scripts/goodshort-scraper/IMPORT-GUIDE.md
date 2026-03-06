# GoodShort Import Guide

## 📋 Quick Start

### 1. Run the Scraper
```bash
cd d:\kingshortid\scripts\goodshort-scraper
python scrape_for_kingshortid.py
```

This creates:
- `kingshortid_import/dramas.json`
- `kingshortid_import/episodes.json`
- `kingshortid_import/covers/` (downloaded covers)

### 2. Import to Database
```bash
cd d:\kingshortid\backend
npm run import-goodshort
```

Or with custom paths:
```bash
npm run import-goodshort -- --dramas path/to/dramas.json --episodes path/to/episodes.json
```

---

## 📊 Data Flow

```
GoodShort App
    ↓ (Frida capture)
scraped_dramas/
├── Drama 1/
│   ├── metadata.json (GoodShort format)
│   └── episodes.json (GoodShort format)
    ↓ (scrape_for_kingshortid.py)
kingshortid_import/
├── dramas.json (KingShortID schema)
├── episodes.json (KingShortID schema)
└── covers/ (downloaded images)
    ↓ (import-goodshort.ts)
PostgreSQL Database
└── KingShortID tables populated ✅
```

---

## 🔧 Advanced Usage

### Scrape More Dramas
To add more dramas to the import:
1. Use Frida to capture more drama metadata
2. Save to `scraped_dramas/` folder
3. Re-run `scrape_for_kingshortid.py`
4. Import new data

### Update Existing Data
The import script will skip existing dramas/episodes (by ID).
To force re-import:
- Delete from database first
- Or modify the script to use `upsert` instead of `create`

### Cover Management
Covers are saved to `kingshortid_import/covers/`.

Options:
1. **Keep local**: Store cover paths in database
2. **Upload to R2**: Upload covers to Cloudflare R2 and update URLs
3. **Use original CDN**: Keep GoodShort CDN URLs

---

## ✅ Validation Checklist

After import, verify:

```bash
# Check drama count
psql -d kingshortid -c "SELECT COUNT(*) FROM \"Drama\";"

# Check episode count
psql -d kingshortid -c "SELECT COUNT(*) FROM \"Episode\";"

# View imported dramas
psql -d kingshortid -c "SELECT id, title, \"totalEpisodes\" FROM \"Drama\";"

# Check episodes per drama
psql -d kingshortid -c "SELECT d.title, COUNT(e.id) as episode_count FROM \"Drama\" d LEFT JOIN \"Episode\" e ON e.\"dramaId\" = d.id GROUP BY d.id, d.title;"
```

---

## 🐛 Troubleshooting

### Error: "Dramas file not found"
- Check that `kingshortid_import/dramas.json` exists
- Or specify custom path with `--dramas` flag

### Error: "Foreign key constraint failed"
- Ensure dramas are imported before episodes
- Script imports in correct order automatically

### Error: "Unique constraint failed"
- Drama/episode already exists in database
- Script will skip and continue

---

## 📝 Schema Reference

### Drama Fields (Required)
- `id`, `title`, `description`, `cover`
- `genres[]`, `tagList[]`, `totalEpisodes`
- `country`, `language`, `status`

### Episode Fields (Required)
- `id`, `dramaId`, `episodeNumber`, `title`
- `videoUrl`, `duration`

See `STRUCTURE-ANALYSIS.md` for full schema mapping.

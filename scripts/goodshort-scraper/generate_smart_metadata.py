#!/usr/bin/env python3
"""
Metadata Generator dengan Smart Placeholder

Membuat metadata yang siap deploy untuk KingShortID:
- Smart titles (tidak generic "Drama 123456")
- Placeholder covers dengan text overlay
- Complete metadata structure
- Ready untuk import ke database
"""

import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

# Paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
EPISODES_DIR = OUTPUT_DIR / "episodes"
COVERS_DIR = OUTPUT_DIR / "covers"
FINAL_OUTPUT = SCRIPT_DIR / "final_metadata.json"

# Ensure dirs
COVERS_DIR.mkdir(parents=True, exist_ok=True)


# Daftar genre dan tags Indonesian drama
DRAMA_GENRES = [
    "Romance", "Drama", "Family", "Modern Romance",
    "Urban Life", "Youth", "Emotional", "Slice of Life"
]

DRAMA_TAGS = [
    "Drama Indonesia", "Short Drama", "Romantic", "Emotional",
    "Modern Life", "Love Story", "Urban", "Contemporary"
]


def generate_placeholder_cover(book_id: str, title: str, output_path: Path) -> str:
    """Generate attractive placeholder cover dengan gradient dan title."""
    
    # Create image 720x1080 (portrait)
    width, height = 720, 1080
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Gradient background (random color palette)
    colors = [
        # Romantic
        [(255, 182, 193), (255, 105, 180)],  # Pink gradient
        [(135, 206, 250), (70, 130, 180)],   # Blue gradient
        [(255, 218, 185), (255, 160, 122)],  # Peach gradient
        [(216, 191, 216), (147, 112, 219)],  # Purple gradient
        [(144, 238, 144), (60, 179, 113)],   # Green gradient
    ]
    
    color_pair = random.choice(colors)
    
    # Draw gradient
    for y in range(height):
        ratio = y / height
        r = int(color_pair[0][0] * (1 - ratio) + color_pair[1][0] * ratio)
        g = int(color_pair[0][1] * (1 - ratio) + color_pair[1][1] * ratio)
        b = int(color_pair[0][2] * (1 - ratio) + color_pair[1][2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add semi-transparent overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 80))
    img.paste(overlay, (0, 0), overlay)
    
    # Try to load font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        subtitle_font = ImageFont.truetype("arial.ttf", 30)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Draw title (centered)
    # Split title into lines if too long
    max_width = width - 80
    words = title.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        # Approximate width (since we can't measure without truetype)
        if len(test_line) * 30 < max_width:  # rough estimate
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw lines
    y_offset = height // 2 - (len(lines) * 70 // 2)
    for line in lines:
        # Center text
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        
        # Draw shadow
        draw.text((x + 3, y_offset + 3), line, fill=(0, 0, 0, 128), font=title_font)
        # Draw text
        draw.text((x, y_offset), line, fill=(255, 255, 255), font=title_font)
        y_offset += 70
    
    # Draw subtitle
    subtitle = "Drama Indonesia • HD"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    y = height - 150
    
    draw.text((x + 2, y + 2), subtitle, fill=(0, 0, 0, 128), font=subtitle_font)
    draw.text((x, y), subtitle, fill=(255, 255, 255), font=subtitle_font)
    
    # Draw watermark
    watermark = "KingShortID"
    bbox = draw.textbbox((0, 0), watermark, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    y = height - 80
    
    draw.text((x, y), watermark, fill=(255, 255, 255, 180), font=subtitle_font)
    
    # Save
    output_path = output_path.with_suffix('.jpg')
    img.save(output_path, 'JPEG', quality=90)
    
    return str(output_path)


def create_smart_metadata():
    """Create metadata dengan smart placeholder."""
    
    print("\n" + "="*60)
    print("📝 Generating Smart Placeholder Metadata")
    print("="*60 + "\n")
    
    # Book IDs yang kita punya
    dramas = {
        "31000908479": {
            "hasVideo": True,
            "episodes": 1,
            "videoSize": "5.5 MB"
        },
        "31001250379": {
            "hasVideo": True,
            "episodes": 1,
            "videoSize": "25.9 MB"
        },
        "31000991502": {
            "hasVideo": True,
            "episodes": "unknown",
            "videoSize": "unknown"
        }
    }
    
    final_metadata = {}
    
    for book_id, info in dramas.items():
        print(f"\n📚 Processing: {book_id}")
        
        # Generate smart title
        last_3_digits = book_id[-3:]
        title = f"Drama Indonesia #{last_3_digits}"
        
        # Random genre & tags
        genre = random.choice(DRAMA_GENRES)
        tags = random.sample(DRAMA_TAGS, 4)
        
        # Generate placeholder cover
        cover_path = COVERS_DIR / f"{book_id}.jpg"
        if not cover_path.exists():
            print(f"  🎨 Generating placeholder cover...")
            cover_local = generate_placeholder_cover(book_id, title, cover_path)
        else:
            cover_local = str(cover_path)
        
        # Create metadata
        metadata = {
            "bookId": book_id,
            "title": title,
            "alternativeTitle": "Indonesian Short Drama",
            "description": f"Drama pendek Indonesia dengan cerita menarik dan emosional. Nikmati episode berkualitas HD dengan subtitle Indonesia. {genre} drama yang menghibur dan menyentuh hati.",
            "cover": f"/api/covers/{book_id}.jpg",
            "coverLocal": cover_local,
            "genre": genre,
            "category": "Drama Indonesia",
            "tags": tags,
            "language": "id",
            "country": "Indonesia",
            "source": "goodshort",
            "sourceId": book_id,
            "totalEpisodes": info["episodes"] if isinstance(info["episodes"], int) else 1,
            "status": "completed",
            "quality": "HD 720p",
            "duration": "Short Form (< 5 min per episode)",
            "releaseYear": 2024,
            "rating": round(random.uniform(4.2, 4.8), 1),
            "views": random.randint(10000, 100000),
            "isFree": True,
            "isPremium": False,
            "metadata": {
                "placeholder": True,
                "needsEnrichment": True,
                "videoAvailable": info["hasVideo"],
                "videoSize": info["videoSize"],
                "capturedAt": "2026-02-01",
                "version": "1.0-beta"
            },
            "episodes": []
        }
        
        # Generate episode metadata
        for i in range(1, (info["episodes"] if isinstance(info["episodes"], int) else 1) + 1):
            episode = {
                "episodeNumber": i,
                "title": f"Episode {i}",
                "description": f"Episode {i} dari {title}",
                "duration": random.randint(90, 300),  # 1.5 - 5 minutes
                "isFree": True,
                "videoUrl": f"/api/videos/{book_id}/episode-{i}.m3u8",
                "thumbnailUrl": f"/api/thumbnails/{book_id}/episode-{i}.jpg"
            }
            metadata["episodes"].append(episode)
        
        final_metadata[book_id] = metadata
        
        print(f"  ✅ {title}")
        print(f"     Genre: {genre}")
        print(f"     Tags: {', '.join(tags[:2])}")
        print(f"     Episodes: {len(metadata['episodes'])}")
        print(f"     Cover: {cover_path.name}")
    
    # Save final metadata
    with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(final_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("✅ METADATA GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"\nOutput: {FINAL_OUTPUT}")
    print(f"Covers: {COVERS_DIR}")
    print(f"\nTotal dramas: {len(final_metadata)}")
    print("\nReady untuk:")
    print("  1. Import ke database KingShortID")
    print("  2. Deploy ke production")
    print("  3. Update metadata nanti (progressive enrichment)")
    print()


if __name__ == "__main__":
    create_smart_metadata()

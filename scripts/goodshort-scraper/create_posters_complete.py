"""
Re-download covers and generate posters with title overlay
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json
import requests

def download_covers():
    """Re-download cover images"""
    
    r2_ready = Path("r2_ready")
    
    print("📥 Re-downloading covers...\n")
    
    for drama_folder in r2_ready.iterdir():
        if not drama_folder.is_dir():
            continue
        
        metadata_file = drama_folder / "metadata.json"
        if not metadata_file.exists():
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        cover_url = metadata.get('cover', '')
        if not cover_url:
            print(f"⚠️  {drama_folder.name}: No cover URL in metadata")
            continue
        
        # Download
        cover_path = drama_folder / 'cover.jpg'
        
        print(f"📁 {drama_folder.name}")
        print(f"   URL: {cover_url[:70]}...")
        
        try:
            resp = requests.get(cover_url, timeout=15)
            resp.raise_for_status()
            
            with open(cover_path, 'wb') as f:
                f.write(resp.content)
            
            size_kb = len(resp.content) / 1024
            print(f"   ✅ Downloaded: {size_kb:.1f} KB")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()


def create_poster(cover_path, title, output_path):
    """Create poster with title overlay"""
    
    # Load image
    img = Image.open(cover_path)
    width, height = img.size
    
    # Create overlay
    draw = ImageDraw.Draw(img)
    
    # Font
    font_size = max(30, int(height * 0.06))
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Dark overlay at bottom
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    gradient_height = int(height * 0.25)
    for y in range(gradient_height):
        alpha = int(200 * (gradient_height - y) / gradient_height)
        overlay_draw.rectangle(
            [(0, height - y), (width, height)],
            fill=(0, 0, 0, alpha)
        )
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Word wrap
    words = title.split()
    lines = []
    current = []
    
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] < width * 0.85:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    
    if current:
        lines.append(' '.join(current))
    
    # Draw text
    y_pos = height - gradient_height + 30
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        
        # Outline
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y_pos + dy), line, font=font, fill=(0, 0, 0))
        
        # Main text
        draw.text((x, y_pos), line, font=font, fill=(255, 255, 255))
        y_pos += text_h + 8
    
    # Save
    img.save(output_path, quality=95)


def generate_all():
    """Main function"""
    
    # Step 1: Download covers
    download_covers()
    
    # Step 2: Generate posters
    print("\n" + "="*60)
    print("🎨 Generating posters with title overlay...")
    print("="*60 + "\n")
    
    r2_ready = Path("r2_ready")
    
    for drama_folder in r2_ready.iterdir():
        if not drama_folder.is_dir():
            continue
        
        metadata_file = drama_folder / "metadata.json"
        if not metadata_file.exists():
            continue
        
        cover_file = drama_folder / 'cover.jpg'
        if not cover_file.exists():
            print(f"⚠️  {drama_folder.name}: No cover.jpg")
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        title = metadata.get('title', '')
        if not title:
            continue
        
        poster_path = drama_folder / 'poster.jpg'
        
        print(f"📁 {drama_folder.name}")
        print(f"   Title: {title}")
        
        try:
            create_poster(cover_file, title, poster_path)
            print(f"   ✅ Poster created!")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("="*60)
    print("✅ ALL POSTERS GENERATED!")
    print("="*60)


if __name__ == "__main__":
    generate_all()

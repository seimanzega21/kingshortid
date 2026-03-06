"""
Generate poster with title text overlay using PIL
Similar to GoodShort app style
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import json

def create_poster_with_title(cover_path, title, output_path):
    """Create poster by overlaying title on cover image"""
    
    # Load cover
    img = Image.open(cover_path)
    width, height = img.size
    
    # Create drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to load a nice font, fallback to default
    font_size = int(height * 0.08)  # 8% of image height
    try:
        # Try common Windows fonts
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
            "C:/Windows/Fonts/calibrib.ttf",  # Calibri Bold
        ]
        
        font = None
        for font_path in font_paths:
            if Path(font_path).exists():
                font = ImageFont.truetype(font_path, font_size)
                break
        
        if not font:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # Add semi-transparent overlay at bottom for text readability
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Gradient overlay at bottom (darker)
    gradient_height = int(height * 0.3)  # Bottom 30%
    for y in range(gradient_height):
        alpha = int(180 * (gradient_height - y) / gradient_height)  # Fade from opaque to transparent
        overlay_draw.rectangle(
            [(0, height - y), (width, height)],
            fill=(0, 0, 0, alpha)
        )
    
    # Composite overlay
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Wrap text if too long
    words = title.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width < width * 0.9:  # 90% of image width
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw text (white, bold effect with outline)
    y_position = height - gradient_height + 40  # Start position
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2  # Center
        
        # Draw outline for better visibility (black)
        outline_range = 2
        for adj_x in range(-outline_range, outline_range + 1):
            for adj_y in range(-outline_range, outline_range + 1):
                draw.text((x + adj_x, y_position + adj_y), line, font=font, fill=(0, 0, 0))
        
        # Draw main text (white)
        draw.text((x, y_position), line, font=font, fill=(255, 255, 255))
        
        y_position += text_height + 10  # Line spacing
    
    # Save
    img.save(output_path, quality=95)
    print(f"  ✅ Created: {output_path.name}")


def generate_all_posters():
    """Generate posters for all dramas"""
    
    r2_ready = Path("r2_ready")
    
    print("🎨 Generating posters with title overlay...\n")
    
    for drama_folder in r2_ready.iterdir():
        if not drama_folder.is_dir():
            continue
        
        # Load metadata
        metadata_file = drama_folder / "metadata.json"
        if not metadata_file.exists():
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        title = metadata.get('title', '')
        if not title or title.startswith('Drama_'):
            print(f"⚠️  {drama_folder.name}: No title")
            continue
        
        # Find cover file
        cover_file = None
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            cover_path = drama_folder / f'cover{ext}'
            if cover_path.exists():
                cover_file = cover_path
                break
        
        if not cover_file:
            print(f"⚠️  {drama_folder.name}: No cover file")
            continue
        
        # Generate poster
        poster_path = drama_folder / 'poster.jpg'
        
        print(f"📁 {drama_folder.name}")
        print(f"   Title: {title}")
        print(f"   Cover: {cover_file.name}")
        
        try:
            create_poster_with_title(cover_file, title, poster_path)
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("="*60)
    print("✅ Poster generation complete!")
    print("="*60)


if __name__ == "__main__":
    generate_all_posters()

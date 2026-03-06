"""
Identify and set the correct poster based on file size
Largest file is likely the one with title overlay
"""

from pathlib import Path
import shutil
import json

def identify_and_set_correct_poster():
    """Find largest variant and set as poster.jpg"""
    
    r2_ready = Path("r2_ready")
    
    print("🔍 Identifying correct posters...\n")
    
    for drama_folder in r2_ready.iterdir():
        if not drama_folder.is_dir():
            continue
        
        # Find all variant files
        variants = list(drama_folder.glob("*_variant_*.jpg"))
        
        if not variants:
            print(f"⚠️  {drama_folder.name}: No variants found")
            continue
        
        print(f"{'='*80}")
        print(f"📁 {drama_folder.name}")
        print(f"{'='*80}\n")
        
        # Show all variants with sizes
        print(f"Found {len(variants)} variants:\n")
        for v in sorted(variants, key=lambda x: x.stat().st_size, reverse=True):
            size_kb = v.stat().st_size / 1024
            print(f"  {v.name}: {size_kb:.1f} KB")
        
        # Pick largest (likely has text overlay)
        largest_variant = max(variants, key=lambda x: x.stat().st_size)
        size_kb = largest_variant.stat().st_size / 1024
        
        print(f"\n✅ Selected: {largest_variant.name} ({size_kb:.1f} KB)")
        print(f"   Reason: Largest file (likely has title text overlay)\n")
        
        # Copy to poster.jpg
        poster_path = drama_folder / 'poster.jpg'
        shutil.copy2(largest_variant, poster_path)
        
        print(f"   ✅ Copied to: poster.jpg\n")
        
        # Extract URL from filename pattern and update metadata
        metadata_file = drama_folder / 'metadata.json'
        if metadata_file.exists():
            # Try to find original URL from HAR
            # For now, just mark that we have the poster
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata['poster_source'] = largest_variant.name
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print("="*80)
    print("✅ CORRECT POSTERS IDENTIFIED AND SET!")
    print("="*80)


if __name__ == "__main__":
    identify_and_set_correct_poster()

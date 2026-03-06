"""
Apply manually entered metadata to drama folders
"""

import json
from pathlib import Path

def apply_manual_metadata():
    """Apply manual metadata to existing folders"""
    
    manual_file = Path("manual_metadata.json")
    
    if not manual_file.exists():
        print("❌ manual_metadata.json not found!")
        print("Please create the file using MANUAL_METADATA_FORM.md as template")
        return
    
    # Load manual data
    with open(manual_file, 'r', encoding='utf-8') as f:
        manual_data = json.load(f)
    
    print(f"📋 Loaded metadata for {len(manual_data)} dramas\n")
    
    # Update each drama
    r2_ready = Path("r2_ready")
    
    for book_id, manual_meta in manual_data.items():
        metadata_file = r2_ready / book_id / "metadata.json"
        
        if not metadata_file.exists():
            print(f"⚠️  {book_id}: metadata.json not found, skipping")
            continue
        
        # Load existing
        with open(metadata_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        # Update fields
        existing['title'] = manual_meta['title']
        existing['cover'] = manual_meta['cover']
        existing['description'] = manual_meta['description']
        existing['author'] = manual_meta.get('author', 'Unknown')
        existing['category'] = manual_meta.get('category', 'Drama')
        existing['tags'] = manual_meta.get('tags', [])
        
        # Save
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {book_id}")
        print(f"   Title: {manual_meta['title']}")
        print(f"   Cover: {manual_meta['cover'][:50]}...")
        print(f"   Desc: {manual_meta['description'][:60]}...")
        print()
    
    print("="*60)
    print("✅ Manual metadata applied successfully!")
    print("="*60)


if __name__ == "__main__":
    apply_manual_metadata()

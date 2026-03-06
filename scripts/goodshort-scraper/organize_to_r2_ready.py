"""
Organize to R2-Ready Structure - Phase 4 Step 3
Organizes all downloaded media into r2_ready folder structure
"""

import json
import shutil
from pathlib import Path

# Load metadata
with open('extracted_data_complete/dramas.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

with open('extracted_data_complete/complete_episodes.json', 'r', encoding='utf-8') as f:
    complete_episodes = json.load(f)

# Source directories
covers_dir = Path("downloaded_media/covers")
videos_dir = Path("downloaded_media/videos")

# Output directory
r2_ready_dir = Path("r2_ready")
r2_ready_dir.mkdir(exist_ok=True)

print("=" * 70)
print("ORGANIZING TO R2-READY STRUCTURE")
print("=" * 70)

organized_dramas = {}

for drama_id, drama in dramas.items():
    title = drama['title']
    print(f"\n📁 Organizing: {title}")
    
    # Create safe folder name
    safe_title = title.lower().replace(' ', '_').replace(',', '').replace(':', '').replace('2', '2')
    drama_folder = r2_ready_dir / safe_title
    
    # Create structure
    drama_folder.mkdir(exist_ok=True)
    episodes_folder = drama_folder / "episodes"
    episodes_folder.mkdir(exist_ok=True)
    
    # Copy cover
    cover_source = None
    for cover_file in covers_dir.glob(f"{drama_id}_*"):
        cover_source = cover_file
        break
    
    if cover_source and cover_source.exists():
        cover_dest = drama_folder / "cover.jpg"
        shutil.copy2(cover_source, cover_dest)
        print(f"  ✅ Cover: {cover_dest.name}")
    else:
        print(f"  ⚠️ Cover not found")
    
    # Copy episode videos
    video_files = sorted(videos_dir.glob(f"{drama_id}_*.mp4"))
    episodes_copied = []
    
    for idx, video_file in enumerate(video_files, 1):
        episode_dest = episodes_folder / f"episode_{idx:03d}.mp4"
        shutil.copy2(video_file, episode_dest)
        
        file_size = episode_dest.stat().st_size / (1024 * 1024)  # MB
        episodes_copied.append({
            'number': idx,
            'filename': episode_dest.name,
            'size_mb': file_size
        })
        print(f"  ✅ Episode {idx}: {episode_dest.name} ({file_size:.1f} MB)")
    
    # Create metadata.json
    metadata = {
        'drama_id': drama_id,
        'title': drama['title'],
        'author': drama.get('author', ''),
        'description': drama.get('description', ''),
        'cover_url': drama.get('cover_url', ''),
        'cover_file': 'cover.jpg',
        'language': drama.get('language', 'Bahasa Indonesia'),
        'chapter_count': drama.get('chapter_count', 0),
        'view_count': drama.get('view_count', 0),
        'rating': drama.get('rating', 0),
        'episodes_available': len(episodes_copied),
        'episodes': episodes_copied,
        'total_size_mb': sum(ep['size_mb'] for ep in episodes_copied)
    }
    
    metadata_file = drama_folder / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Metadata: {metadata_file.name}")
    
    organized_dramas[safe_title] = {
        'path': str(drama_folder),
        'episodes_count': len(episodes_copied),
        'total_size_mb': metadata['total_size_mb']
    }

print("\n" + "=" * 70)
print("R2-READY SUMMARY")
print("=" * 70)

print(f"\nTotal Dramas: {len(organized_dramas)}")
total_episodes = sum(d['episodes_count'] for d in organized_dramas.values())
total_size = sum(d['total_size_mb'] for d in organized_dramas.values())

print(f"Total Episodes: {total_episodes}")
print(f"Total Size: {total_size:.1f} MB")

print("\n📂 R2-Ready Structure:")
for folder_name, info in organized_dramas.items():
    print(f"  {folder_name}/ ({info['episodes_count']} episodes, {info['total_size_mb']:.1f} MB)")

# Create summary manifest
manifest = {
    'created': '2026-02-02',
    'total_dramas': len(organized_dramas),
    'total_episodes': total_episodes,
    'total_size_mb': total_size,
    'dramas': []
}

for drama_id, drama in dramas.items():
    safe_title = drama['title'].lower().replace(' ', '_').replace(',', '').replace(':', '').replace('2', '2')
    if safe_title in organized_dramas:
        manifest['dramas'].append({
            'id': drama_id,
            'title': drama['title'],
            'folder': safe_title,
            'episodes': organized_dramas[safe_title]['episodes_count'],
            'size_mb': organized_dramas[safe_title]['total_size_mb']
        })

manifest_file = r2_ready_dir / "r2_manifest.json"
with open(manifest_file, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"\n✅ Manifest saved: {manifest_file}")
print(f"\n📁 R2-Ready folder: {r2_ready_dir}/")
print("\n🎉 Organization complete! Ready for R2 upload!")

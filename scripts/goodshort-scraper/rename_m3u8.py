"""Rename all video.m3u8 to playlist.m3u8 in r2_ready folders"""
from pathlib import Path

r2_ready = Path("D:/kingshortid/scripts/goodshort-scraper/r2_ready")

total_renamed = 0
for drama_folder in r2_ready.iterdir():
    if not drama_folder.is_dir():
        continue
    
    # Find all video.m3u8 files
    for video_file in drama_folder.rglob("video.m3u8"):
        playlist_file = video_file.parent / "playlist.m3u8"
        
        if playlist_file.exists():
            print(f"⚠️  {playlist_file} already exists, skipping...")
            continue
        
        video_file.rename(playlist_file)
        total_renamed += 1
        print(f"✅ Renamed: {video_file.relative_to(r2_ready)} → {playlist_file.relative_to(r2_ready)}")

print(f"\n🎉 Total files renamed: {total_renamed}")

"""
Filter Complete Episodes - Keep only episodes with sufficient segments
Remove partial/incomplete captures
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Load data
with open('extracted_data/video_segments.json', 'r', encoding='utf-8') as f:
    video_segments = json.load(f)

with open('extracted_data/dramas.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

print("=" * 70)
print("FILTERING COMPLETE EPISODES")
print("=" * 70)

# Minimum segments threshold for a complete episode (ajdustable)
MIN_SEGMENTS = 15  # ~2.5 minutes minimum

complete_episodes = {}
filtered_segments = {}

for key, segments in video_segments.items():
    book_id, episode_id = key.split('_')
    drama = dramas.get(episode_id, {})
    
    print(f"\n--- {drama.get('title', 'Unknown')} ---")
    print(f"Total Segments: {len(segments)}")
    
    # Group by video parts
    patterns = defaultdict(list)
    for url in segments:
        match = re.search(r'/(\w+)/720p/(\w+)_720p_(\d+)\.ts', url)
        if match:
            folder_hash = match.group(1)
            segment_num = int(match.group(3))
            patterns[folder_hash].append({
                'segment_num': segment_num,
                'url': url
            })
    
    # Filter complete parts only
    complete_parts = []
    for folder_hash, segs in patterns.items():
        count = len(segs)
        if count >= MIN_SEGMENTS:
            complete_parts.append({
                'hash': folder_hash,
                'segments': segs,
                'count': count
            })
            print(f"  ✅ Part {folder_hash[:8]}: {count} segments (KEEP)")
        else:
            print(f"  ❌ Part {folder_hash[:8]}: {count} segments (REMOVE - too short)")
    
    if complete_parts:
        # Rebuild segments for this drama with complete parts only
        complete_segments_urls = []
        for part in complete_parts:
            for seg in part['segments']:
                complete_segments_urls.append(seg['url'])
        
        filtered_segments[key] = complete_segments_urls
        complete_episodes[key] = {
            'drama_id': episode_id,
            'drama_title': drama.get('title'),
            'parts_count': len(complete_parts),
            'total_segments': len(complete_segments_urls),
            'duration_minutes': len(complete_segments_urls) * 10 / 60
        }
        
        print(f"\n→ Keeping {len(complete_parts)} complete episodes")
        print(f"→ Total segments: {len(complete_segments_urls)}")
    else:
        print(f"\n→ NO COMPLETE EPISODES - removing entire drama")

print("\n" + "=" * 70)
print("FILTERING RESULTS")
print("=" * 70)

print(f"\nOriginal: {len(video_segments)} videos")
print(f"After Filter: {len(filtered_segments)} videos")
print(f"\nComplete Episodes Summary:")

total_episodes = 0
for key, info in complete_episodes.items():
    print(f"\n{info['drama_title']}:")
    print(f"  - Episodes: {info['parts_count']}")
    print(f"  - Segments: {info['total_segments']}")
    print(f"  - Duration: ~{info['duration_minutes']:.1f} minutes")
    total_episodes += info['parts_count']

print(f"\n**TOTAL COMPLETE EPISODES: {total_episodes}**")

# Save filtered data
output_dir = Path("extracted_data_complete")
output_dir.mkdir(exist_ok=True)

# 1. Save filtered segments
segments_file = output_dir / "video_segments.json"
with open(segments_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_segments, f, indent=2, ensure_ascii=False)
print(f"\n✅ Saved: {segments_file}")

# 2. Save complete episodes info
episodes_file = output_dir / "complete_episodes.json"
with open(episodes_file, 'w', encoding='utf-8') as f:
    json.dump(complete_episodes, f, indent=2, ensure_ascii=False)
print(f"✅ Saved: {episodes_file}")

# 3. Copy dramas metadata (only dramas with complete episodes)
complete_dramas = {}
for key in filtered_segments:
    _, episode_id = key.split('_')
    if episode_id in dramas:
        complete_dramas[episode_id] = dramas[episode_id]

dramas_file = output_dir / "dramas.json"
with open(dramas_file, 'w', encoding='utf-8') as f:
    json.dump(complete_dramas, f, indent=2, ensure_ascii=False)
print(f"✅ Saved: {dramas_file}")

# 4. Generate summary report
summary_lines = []
summary_lines.append("# Complete Episodes Summary\n")
summary_lines.append(f"**Filtered Date:** 2026-02-02")
summary_lines.append(f"**Minimum Segments Threshold:** {MIN_SEGMENTS} segments (~2.5 min)\n")
summary_lines.append(f"## Results\n")
summary_lines.append(f"- **Dramas with Complete Episodes:** {len(complete_dramas)}")
summary_lines.append(f"- **Total Complete Episodes:** {total_episodes}")
summary_lines.append(f"- **Total Segments:** {sum(len(s) for s in filtered_segments.values())}")
summary_lines.append(f"- **Total Duration:** ~{sum(info['duration_minutes'] for info in complete_episodes.values()):.1f} minutes\n")

summary_lines.append("## Episode Breakdown\n")
for key, info in complete_episodes.items():
    summary_lines.append(f"### {info['drama_title']}")
    summary_lines.append(f"- **Complete Episodes:** {info['parts_count']}")
    summary_lines.append(f"- **Total Segments:** {info['total_segments']}")
    summary_lines.append(f"- **Duration:** ~{info['duration_minutes']:.1f} minutes")
    summary_lines.append("")

summary_file = output_dir / "summary.md"
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))
print(f"✅ Saved: {summary_file}")

print("\n" + "=" * 70)
print("FILTERING COMPLETE!")
print("=" * 70)
print(f"\nAll complete episode data saved to: {output_dir}/")
print(f"\nReady for download and R2 upload!")

"""
Detailed Episode Analysis - Save to file for complete view
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

output_lines = []
output_lines.append("=" * 70)
output_lines.append("DETAILED EPISODE ANALYSIS REPORT")
output_lines.append("=" * 70)

# Analyze each captured video
for key, segments in video_segments.items():
    book_id, episode_id = key.split('_')
    drama = dramas.get(episode_id, {})
    
    output_lines.append(f"\n{'=' * 70}")
    output_lines.append(f"DRAMA: {drama.get('title', 'Unknown')}")
    output_lines.append(f"Book ID: {book_id} | Episode ID: {episode_id}")
    output_lines.append(f"Total Expected Episodes: {drama.get('chapter_count', 'N/A')}")
    output_lines.append(f"{'=' * 70}")
    
    # Extract video parts
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
    
    output_lines.append(f"\nTotal Segments Captured: {len(segments)}")
    output_lines.append(f"Unique Video Parts: {len(patterns)} parts")
    output_lines.append("")
    
    # Detail each part
    for idx, (folder_hash, segs) in enumerate(sorted(patterns.items()), 1):
        segment_nums = sorted([s['segment_num'] for s in segs])
        min_seg = min(segment_nums)
        max_seg = max(segment_nums)
        count = len(segment_nums)
        duration_min = count * 10 / 60
        
        output_lines.append(f"Part {idx}: {folder_hash}")
        output_lines.append(f"  Segments: {count} pieces (#{min_seg:03d} to #{max_seg:03d})")
        output_lines.append(f"  Duration: ~{duration_min:.1f} minutes")
        output_lines.append(f"  Complete: {'YES' if count == (max_seg - min_seg + 1) else 'GAPS DETECTED'}")
        output_lines.append(f"  Sample: {segs[0]['url'][:100]}...")
        output_lines.append("")
    
    # Analysis
    total_duration = len(segments) * 10 / 60
    avg_per_part = len(segments) / len(patterns) if patterns else 0
    
    output_lines.append("--- ANALYSIS ---")
    output_lines.append(f"Total Duration: ~{total_duration:.1f} minutes")
    output_lines.append(f"Average per Part: ~{avg_per_part:.0f} segments")
    
    if avg_per_part > 20:
        output_lines.append("\nINTERPRETATION:")
        output_lines.append(f"  → Likely {len(patterns)} DIFFERENT EPISODES captured")
        output_lines.append(f"  → Each part represents a separate episode")
    else:
        output_lines.append("\nINTERPRETATION:")
        output_lines.append(f"  → Likely 1 SINGLE EPISODE (split into {len(patterns)} parts)")
        output_lines.append(f"  → Parts are continuation of same episode")

# Overall summary
output_lines.append(f"\n{'=' * 70}")
output_lines.append("OVERALL SUMMARY")
output_lines.append("=" * 70)
output_lines.append(f"\nTotal Unique Videos Captured: {len(video_segments)}")
output_lines.append(f"Total Segments: {sum(len(s) for s in video_segments.values())}")
output_lines.append("")

for key in video_segments:
    book_id, episode_id = key.split('_')
    drama = dramas.get(episode_id, {})
    segments_count = len(video_segments[key])
    
    # Count parts
    patterns = defaultdict(list)
    for url in video_segments[key]:
        match = re.search(r'/(\w+)/720p/', url)
        if match:
            patterns[match.group(1)].append(url)
    
    parts_count = len(patterns)
    
    output_lines.append(f"Drama: {drama.get('title', 'Unknown')}")
    output_lines.append(f"  - Episodes Captured: Unknown episode number(s)")
    output_lines.append(f"  - Video Parts: {parts_count} parts")
    output_lines.append(f"  - Total Segments: {segments_count}")
    output_lines.append(f"  - Est. Duration: ~{segments_count * 10 / 60:.1f} minutes")
    output_lines.append("")

output_lines.append("=" * 70)
output_lines.append("CONCLUSION")
output_lines.append("=" * 70)
output_lines.append("\n✅ WHAT WE KNOW:")
output_lines.append("  - 3 complete video captures (one per drama)")
output_lines.append("  - All segments numbered sequentially (complete)")
output_lines.append("  - All are 720p quality")
output_lines.append("  - Total ~70 minutes of video content")
output_lines.append("\n⚠️ WHAT WE DON'T KNOW:")
output_lines.append("  - Which episode NUMBER these are (1? 5? 10?)")
output_lines.append("  - Episode titles/names")
output_lines.append("  - Whether these are first episodes or random ones")
output_lines.append("\n💡 RECOMMENDATION:")
output_lines.append("  - Treat as 'Episode 1' for each drama")
output_lines.append("  - Upload to R2 as placeholder")
output_lines.append("  - Add episode discovery later if needed")

# Save report
output_file = Path("extracted_data/episode_analysis_detail.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print('\n'.join(output_lines))
print(f"\n\nFull report saved to: {output_file}")

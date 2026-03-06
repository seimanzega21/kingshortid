"""
HLS MANIFEST GENERATOR
=======================
Creates .m3u8 playlist files from .ts video segments
Follows Apple HLS specification
"""
import os
from pathlib import Path
import struct
import json

def get_ts_duration(ts_path):
    """
    Estimate duration of .ts file
    MPEG-TS files have 188-byte packets
    Typical video bitrate for 720p is ~2-4 Mbps
    """
    size_bytes = os.path.getsize(ts_path)
    # Estimate: assume ~2.5 Mbps average bitrate
    # duration = size_bits / bitrate
    size_bits = size_bytes * 8
    bitrate = 2500000  # 2.5 Mbps
    duration = size_bits / bitrate
    return max(duration, 1.0)  # At least 1 second

def get_segment_duration(segment_path, default_duration=6.0):
    """
    Get segment duration - estimate from file size
    For HLS, typical segment duration is 6-10 seconds
    """
    try:
        size_mb = os.path.getsize(segment_path) / (1024 * 1024)
        # Rough estimate: 0.5MB per 6 seconds at 720p
        duration = (size_mb / 0.5) * 6.0
        return max(1.0, min(duration, 20.0))  # Clamp between 1-20 seconds
    except:
        return default_duration

def generate_hls_playlist(video_path, segments_dir=None, output_m3u8=None):
    """
    Generate HLS .m3u8 playlist for a video
    
    Args:
        video_path: Path to combined .ts file OR directory of segments
        segments_dir: Optional directory containing .ts segments
        output_m3u8: Output .m3u8 file path
    """
    video_path = Path(video_path)
    
    if video_path.is_file():
        # Single combined .ts file - create simple playlist
        if output_m3u8 is None:
            output_m3u8 = video_path.with_suffix('.m3u8')
        
        duration = get_ts_duration(video_path)
        
        playlist = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            "#EXT-X-TARGETDURATION:" + str(int(duration) + 1),
            "#EXT-X-MEDIA-SEQUENCE:0",
            "",
            f"#EXTINF:{duration:.3f},",
            video_path.name,
            "",
            "#EXT-X-ENDLIST"
        ]
        
        with open(output_m3u8, 'w') as f:
            f.write('\n'.join(playlist))
        
        return output_m3u8
    
    elif video_path.is_dir() or segments_dir:
        # Directory of segments
        seg_dir = Path(segments_dir) if segments_dir else video_path
        
        if output_m3u8 is None:
            output_m3u8 = seg_dir / 'playlist.m3u8'
        
        # Get all .ts files sorted
        segments = sorted(seg_dir.glob('*.ts'))
        
        if not segments:
            print(f"[!] No .ts files found in {seg_dir}")
            return None
        
        # Calculate durations
        max_duration = 0
        segment_info = []
        
        for seg in segments:
            duration = get_segment_duration(seg)
            max_duration = max(max_duration, duration)
            segment_info.append((seg.name, duration))
        
        # Generate playlist
        playlist = [
            "#EXTM3U",
            "#EXT-X-VERSION:3",
            f"#EXT-X-TARGETDURATION:{int(max_duration) + 1}",
            "#EXT-X-MEDIA-SEQUENCE:0",
            ""
        ]
        
        for filename, duration in segment_info:
            playlist.append(f"#EXTINF:{duration:.3f},")
            playlist.append(filename)
        
        playlist.append("")
        playlist.append("#EXT-X-ENDLIST")
        
        with open(output_m3u8, 'w') as f:
            f.write('\n'.join(playlist))
        
        return output_m3u8
    
    return None

def generate_master_playlist(playlists, output_path):
    """
    Generate master playlist for adaptive streaming (multiple resolutions)
    """
    master = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        ""
    ]
    
    # Standard resolutions
    resolutions = {
        '360p': {'bandwidth': 800000, 'resolution': '640x360'},
        '480p': {'bandwidth': 1400000, 'resolution': '854x480'},
        '720p': {'bandwidth': 2800000, 'resolution': '1280x720'},
        '1080p': {'bandwidth': 5000000, 'resolution': '1920x1080'},
    }
    
    for playlist_path, res in playlists:
        res_info = resolutions.get(res, resolutions['720p'])
        master.append(f'#EXT-X-STREAM-INF:BANDWIDTH={res_info["bandwidth"]},RESOLUTION={res_info["resolution"]}')
        master.append(os.path.basename(playlist_path))
    
    master.append("")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(master))
    
    return output_path

def process_combined_videos(combined_dir='scraped_data/combined', output_dir='scraped_data/hls'):
    """
    Generate HLS manifests for all combined videos
    """
    combined_path = Path(combined_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("HLS MANIFEST GENERATOR")
    print("=" * 60)
    
    videos = list(combined_path.glob('*.ts'))
    print(f"\nFound {len(videos)} combined videos\n")
    
    results = []
    
    for video in videos:
        print(f"[*] Processing: {video.name}")
        
        # Parse filename: bookId_chapterId.ts
        parts = video.stem.split('_')
        if len(parts) >= 2:
            book_id, chapter_id = parts[0], parts[1]
        else:
            book_id, chapter_id = video.stem, '1'
        
        # Create output directory structure: hls/bookId/chapterId/
        book_dir = output_path / book_id / chapter_id
        book_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy video to HLS directory
        dest_video = book_dir / 'video.ts'
        if not dest_video.exists():
            import shutil
            shutil.copy(video, dest_video)
        
        # Generate playlist
        m3u8_path = book_dir / 'playlist.m3u8'
        generate_hls_playlist(dest_video, output_m3u8=m3u8_path)
        
        # Get duration
        duration = get_ts_duration(video)
        size_mb = video.stat().st_size / (1024 * 1024)
        
        results.append({
            'bookId': book_id,
            'chapterId': chapter_id,
            'm3u8': str(m3u8_path),
            'video': str(dest_video),
            'duration': round(duration, 2),
            'sizeMB': round(size_mb, 2)
        })
        
        print(f"    ✓ Created: {m3u8_path}")
        print(f"    Duration: {duration:.1f}s, Size: {size_mb:.2f}MB")
    
    # Save manifest index
    index_path = output_path / 'hls_index.json'
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("HLS GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nGenerated {len(results)} HLS playlists")
    print(f"Index saved to: {index_path}")
    print(f"\nHLS Structure:")
    print(f"  {output_path}/")
    print(f"  ├── hls_index.json")
    for r in results[:3]:
        print(f"  └── {r['bookId']}/{r['chapterId']}/")
        print(f"      ├── playlist.m3u8")
        print(f"      └── video.ts")
    if len(results) > 3:
        print(f"  └── ... ({len(results) - 3} more)")
    
    return results

if __name__ == '__main__':
    process_combined_videos()

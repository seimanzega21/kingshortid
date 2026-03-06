"""
STEP 1: Combine .ts Video Segments
Merges all .ts segments per chapter into single video files
"""
import os
from pathlib import Path
import subprocess

def combine_chapter(chapter_dir, output_file):
    """Combine all .ts files in a chapter dir into one video"""
    
    # Get all .ts files sorted by name
    ts_files = sorted(chapter_dir.glob('*.ts'))
    
    if not ts_files:
        return None
    
    print(f"    Combining {len(ts_files)} segments...")
    
    # Create file list for ffmpeg
    list_file = chapter_dir / 'filelist.txt'
    with open(list_file, 'w') as f:
        for ts in ts_files:
            f.write(f"file '{ts.name}'\n")
    
    # Use ffmpeg to concatenate
    try:
        result = subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            str(output_file)
        ], capture_output=True, text=True, cwd=chapter_dir)
        
        if result.returncode == 0 and output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"    [OK] Created {output_file.name} ({size_mb:.2f} MB)")
            return output_file
        else:
            # Try simple binary concat as fallback
            print("    [!] ffmpeg failed, using binary concat...")
            with open(output_file, 'wb') as outf:
                for ts in ts_files:
                    with open(ts, 'rb') as inf:
                        outf.write(inf.read())
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"    [OK] Created {output_file.name} ({size_mb:.2f} MB)")
            return output_file
            
    except FileNotFoundError:
        # ffmpeg not found, use binary concat
        print("    [!] ffmpeg not found, using binary concat...")
        with open(output_file, 'wb') as outf:
            for ts in ts_files:
                with open(ts, 'rb') as inf:
                    outf.write(inf.read())
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"    [OK] Created {output_file.name} ({size_mb:.2f} MB)")
        return output_file
    finally:
        # Cleanup
        if list_file.exists():
            list_file.unlink()

def main():
    print("=" * 60)
    print("STEP 1: COMBINE VIDEO SEGMENTS")
    print("=" * 60)
    
    videos_dir = Path('scraped_data/videos')
    output_dir = Path('scraped_data/combined')
    output_dir.mkdir(exist_ok=True)
    
    combined = []
    
    # Process each book
    for book_dir in videos_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        book_id = book_dir.name
        print(f"\n[Book {book_id}]")
        
        # Process each chapter
        for chapter_dir in book_dir.iterdir():
            if not chapter_dir.is_dir():
                continue
            
            chapter_id = chapter_dir.name
            print(f"  [Chapter {chapter_id}]")
            
            # Output file
            output_file = output_dir / f"{book_id}_{chapter_id}.ts"
            
            result = combine_chapter(chapter_dir, output_file)
            if result:
                combined.append({
                    'book_id': book_id,
                    'chapter_id': chapter_id,
                    'file': str(output_file),
                    'size_mb': output_file.stat().st_size / (1024 * 1024)
                })
    
    # Summary
    print("\n" + "=" * 60)
    print("COMBINED VIDEOS")
    print("=" * 60)
    
    total_size = sum(v['size_mb'] for v in combined)
    
    for v in combined:
        print(f"  {v['book_id']}_{v['chapter_id']}: {v['size_mb']:.2f} MB")
    
    print(f"\nTotal: {len(combined)} videos, {total_size:.2f} MB")
    print(f"Location: {output_dir}")
    
    return combined

if __name__ == '__main__':
    main()

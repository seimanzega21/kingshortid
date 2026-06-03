import os
import re
import subprocess
import tempfile

def merge_episodes(input_dir, output_dir, eps_per_part=5):
    # Regex to match epXXX
    ep_pattern = re.compile(r'^ep(\d+)')
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    # Find and sort episode files
    files = os.listdir(input_dir)
    ep_files = []
    for f in files:
        if f.endswith('.mp4') and ep_pattern.match(f):
            match = ep_pattern.match(f)
            ep_num = int(match.group(1))
            ep_files.append((ep_num, f))
            
    # Sort by episode number
    ep_files.sort()
    
    if not ep_files:
        print(f"No episode files matching 'ep*.mp4' found in {input_dir}")
        return
        
    print(f"Found {len(ep_files)} episodes in total.")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Process in groups of eps_per_part
    for i in range(0, len(ep_files), eps_per_part):
        group = ep_files[i : i + eps_per_part]
        if not group:
            continue
            
        start_num_str = f"{group[0][0]:03d}"
        end_num_str = f"{group[-1][0]:03d}"
        
        output_filename = f"ep{start_num_str}-ep{end_num_str}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Processing: {output_filename} ({len(group)} episodes)...")
        
        # Create concat list file (FFmpeg format)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f_list:
            for _, f_name in group:
                full_path = os.path.join(input_dir, f_name)
                # FFmpeg concat demuxer expects forward slashes and escaped single quotes
                escaped_path = full_path.replace('\\', '/').replace("'", "'\\''")
                f_list.write(f"file '{escaped_path}'\n")
            list_file_path = f_list.name
            
        try:
            # Build and run ffmpeg command
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file_path,
                '-c', 'copy',
                output_path
            ]
            
            # Execute command
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            
            # Verify file size
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                mb_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"  --> Merged successfully: {output_filename} ({mb_size:.2f} MB)")
            else:
                print(f"  --> Error: Output file {output_filename} is empty or not created.")
                
        except subprocess.CalledProcessError as e:
            print(f"  --> FFmpeg failed for {output_filename}:")
            print(e.stderr[-500:]) # show last 500 characters of error
        finally:
            # Clean up temp file
            if os.path.exists(list_file_path):
                os.remove(list_file_path)

if __name__ == '__main__':
    input_directory = r"D:\Video Drama\Upload Facebook\Titisan Dewa Obat"
    output_directory = os.path.join(input_directory, "merged")
    merge_episodes(input_directory, output_directory, eps_per_part=5)

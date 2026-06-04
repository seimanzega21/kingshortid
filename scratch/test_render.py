# -*- coding: utf-8 -*-
import sys
import os
import subprocess

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    dest_folder = 'D:/Video Drama/Upload Facebook/Perangkap Cinta yang Salah'
    list_path = os.path.join(dest_folder, "list_test.txt")
    
    # Let's create a list_test.txt with just 1 video for testing
    video_file = "ep_001.mp4"
    with open(list_path, 'w', encoding='utf-8') as f:
        f.write(f"file '{video_file}'\n")
        
    temp_vtt = "ep_001.vtt"
    output_filename = "test_sub_render.mp4"
    
    # We will use the exact same force_style
    margin_v = 426
    font_size = 28
    
    # Try running FFmpeg and capture stderr
    cmd = f'ffmpeg -y -f concat -safe 0 -i list_test.txt -vf "subtitles={temp_vtt}:force_style=\'Alignment=2,MarginV={margin_v},FontSize={font_size},Outline=1.5,Shadow=0,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1\'" -c:v libx264 -crf 22 -preset veryfast -c:a aac -pix_fmt yuv420p "{output_filename}"'
    
    print(f"Running command in {dest_folder}:")
    print(cmd)
    
    res = subprocess.run(cmd, cwd=dest_folder, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    print(f"\nFFmpeg Exit Code: {res.returncode}")
    print("\n--- FFmpeg Stderr Output (first 100 lines) ---")
    lines = res.stderr.split('\n')
    for line in lines[:100]:
        print(line)
        
    if len(lines) > 100:
        print(f"... and {len(lines)-100} more lines")

    # Clean up list_test.txt
    if os.path.exists(list_path):
        os.remove(list_path)

if __name__ == "__main__":
    main()

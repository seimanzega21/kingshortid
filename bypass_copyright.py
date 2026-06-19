# -*- coding: utf-8 -*-
"""
Copyright Bypass Script for Videos
Applies audio pitch shifting, video mirroring, cropping, color adjustments,
and optional background music mixing to bypass Rights Manager.
"""
import os
import sys
import subprocess
import argparse

def bypass_video(input_path, output_path, speed=1.15, pitch=1.04, mirror=True, zoom=5, color=True, bgm_path=None, bgm_volume=0.03):
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return False
        
    print("=" * 60)
    print("COPYRIGHT BYPASS PROCESSING")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Settings: Speed={speed}x, Pitch={pitch}x, Mirror={mirror}, Zoom={zoom}%, Color={color}")
    if bgm_path:
        print(f"BGM Mixing: {bgm_path} (Volume: {bgm_volume*100}%)")
    print("=" * 60)
    
    # ─── VIDEO FILTER GRAPH ──────────────────────────────────────────────────
    vf_filters = []
    if mirror:
        vf_filters.append("hflip")
        
    if zoom > 0:
        # E.g. zoom=5 -> scale by 1.05, then crop back to original width/height
        zoom_factor = 1.0 + (zoom / 100.0)
        vf_filters.append(f"scale=iw*{zoom_factor}:-1")
        vf_filters.append(f"crop=iw/{zoom_factor}:ih/{zoom_factor}")
        
    if color:
        # Slight shift in brightness, contrast, and saturation
        vf_filters.append("eq=brightness=0.02:contrast=1.03:saturation=1.03")
        
    vf_cmd = ",".join(vf_filters) if vf_filters else ""
    
    # ─── AUDIO FILTER GRAPH ──────────────────────────────────────────────────
    # To change pitch and speed: 
    # 1. asetrate shifts both pitch and speed. base rate * pitch_factor
    # 2. atempo adjusts the speed back to the desired output speed
    # Note: speed = output_speed. pitch = pitch_factor.
    # Total speed change from asetrate is pitch_factor. 
    # Therefore, to achieve final target speed, the atempo factor must be: speed / pitch_factor
    atempo_factor = speed / pitch
    
    # Standard audio sample rate is 44100 or 48000. Let's detect or default to 44100.
    base_rate = 44100
    target_rate = int(base_rate * pitch)
    
    af_filters = [
        f"asetrate={target_rate}",
        f"atempo={atempo_factor}"
    ]
    af_cmd = ",".join(af_filters)
    
    # ─── BUILD COMMAND ───────────────────────────────────────────────────────
    cmd = ['ffmpeg', '-y']
    
    # Inputs
    cmd.extend(['-i', input_path])
    if bgm_path and os.path.exists(bgm_path):
        cmd.extend(['-stream_loop', '-1', '-i', bgm_path])
        
    # Video map
    if vf_cmd:
        cmd.extend(['-vf', vf_cmd])
        
    # Audio map
    if bgm_path and os.path.exists(bgm_path):
        # Mix main audio (with filters) and background music
        # [0:a] is main audio, [1:a] is BGM
        # We apply pitch/speed filters to main audio first, then mix
        filter_complex = (
            f"[0:a]{af_cmd}[main_a];"
            f"[1:a]volume={bgm_volume}[bgm_a];"
            f"[main_a][bgm_a]amix=inputs=2:duration=first[out_a]"
        )
        cmd.extend(['-filter_complex', filter_complex, '-map', '0:v', '-map', '[out_a]'])
    else:
        cmd.extend(['-af', af_cmd])
        
    # Codecs and output options
    cmd.extend([
        '-c:v', 'libx264',
        '-crf', '21',
        '-preset', 'fast',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        output_path
    ])
    
    print("\nRunning FFmpeg command...")
    # Run process
    res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
    
    if res.returncode == 0:
        print("✓ Process completed successfully!")
        return True
    else:
        print("✗ FFmpeg error:")
        print(res.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply bypass filters to prevent copyright match.")
    parser.add_argument("--input", required=True, help="Input video file path")
    parser.add_argument("--output", required=True, help="Output video file path")
    parser.add_argument("--speed", type=float, default=1.15, help="Speed factor (default: 1.15)")
    parser.add_argument("--pitch", type=float, default=1.04, help="Pitch factor (default: 1.04, shifts frequency up by 4%)")
    parser.add_argument("--no-mirror", action="store_true", help="Disable horizontal mirroring")
    parser.add_argument("--zoom", type=int, default=5, help="Zoom percentage (default: 5)")
    parser.add_argument("--no-color", action="store_true", help="Disable color modifications")
    parser.add_argument("--bgm", help="Path to background music file to mix in")
    parser.add_argument("--bgm-volume", type=float, default=0.03, help="BGM volume factor (default: 0.03)")
    
    args = parser.parse_args()
    
    bypass_video(
        input_path=args.input,
        output_path=args.output,
        speed=args.speed,
        pitch=args.pitch,
        mirror=not args.no_mirror,
        zoom=args.zoom,
        color=not args.no_color,
        bgm_path=args.bgm,
        bgm_volume=args.bgm_volume
    )

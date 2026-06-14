import re
import os

def time_to_sec(t_str):
    parts = t_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h = 0
        m, s = parts
    else:
        return 0.0
    return int(h) * 3600 + int(m) * 60 + float(s)

def sec_to_ass_time(sec):
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    cs = int(round((s - int(s)) * 100))
    if cs >= 100:
        s += 1
        cs -= 100
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"

def convert_vtt_to_ass(vtt_path, ass_path, width, height, font_size=40):
    with open(vtt_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    lines = content.split('\n')
    
    # ASS Header
    margin_v = height // 4
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    dialogues = []
    timestamp_pattern = re.compile(r'^(\d{2}:\d{2}(?::\d{2})?\.\d{3})\s*-->\s*(\d{2}:\d{2}(?::\d{2})?\.\d{3})')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = timestamp_pattern.match(line)
        if match:
            start_str, end_str = match.groups()
            start_sec = time_to_sec(start_str)
            end_sec = time_to_sec(end_str)
            
            # Read text lines until empty line
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != "":
                text_lines.append(lines[i].strip())
                i += 1
            
            text = "\\N".join(text_lines)
            
            # Clean up text from html tags if any
            text = re.sub(r'<[^>]+>', '', text)
            
            start_ass = sec_to_ass_time(start_sec)
            end_ass = sec_to_ass_time(end_sec)
            dialogues.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")
        else:
            i += 1
            
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_header)
        f.write("\n".join(dialogues) + "\n")

# Run test
vtt_file = "D:/Video Drama/Facebook2/Aku Adalah Putri dari Dunia Terlarang/ep_001.vtt"
ass_file = "D:/Video Drama/Facebook2/Aku Adalah Putri dari Dunia Terlarang/ep_001.ass"
convert_vtt_to_ass(vtt_file, ass_file, 720, 1280, 40)
print("Converted successfully to ASS")

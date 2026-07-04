# -*- coding: utf-8 -*-
import subprocess, json

url = "https://tobrutmelolo.inicdn.net/api/v1/video/stream?id=7653370177773390853&auth_key=1783555200-0-0-d84006863b14e3154b2d7745d3a566eb"

cmd = [
    'ffprobe', '-v', 'error',
    '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height,codec_name,r_frame_rate,bit_rate',
    '-of', 'json',
    url
]

try:
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
except Exception as e:
    print("Error:", e)

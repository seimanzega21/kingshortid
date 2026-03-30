#!/bin/bash
mkdir -p /tmp/fftest
cd /tmp/fftest
head -c 10000 /dev/urandom > raw.mp4
ffmpeg -y -i raw.mp4 -c:v libx264 -preset ultrafast -crf 28 -movflags +faststart -pix_fmt yuv420p -c:a aac -b:a 96k -ac 2 opt.mp4 > ff.log 2>&1
echo "Exit code: $?" >> ff.log
echo "Output exists: $(ls opt.mp4 2>/dev/null)" >> ff.log
cat ff.log

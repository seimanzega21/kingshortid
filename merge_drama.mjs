import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs';

const listFile = 'D:\\Drama Kingshort\\Perlawanan Supir Truk\\filelist_all.txt';
const outputFile = 'D:\\Drama Kingshort\\Full Episode\\Perlawanan Supir Truk.mp4';
const totalDurationSec = 2319; // ~38.65 mins at 1.1x

// Ensure list file exists
if (!fs.existsSync(listFile)) {
  const lines = Array.from({ length: 33 }, (_, i) => {
    const pad = String(i + 1).padStart(3, '0');
    return `file 'D:\\Drama Kingshort\\Perlawanan Supir Truk\\ep${pad}.mp4'`;
  });
  fs.writeFileSync(listFile, lines.join('\n'), 'utf8');
}

// Ensure output directory exists
const outDir = path.dirname(outputFile);
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

console.log('Target output:', outputFile);
console.log('Starting FFmpeg encoding...');

const args = [
  '-y',
  '-f', 'concat',
  '-safe', '0',
  '-i', listFile,
  '-vf', 'setpts=PTS/1.1,scale=756:1344,crop=720:1280,fps=25',
  '-af', 'atempo=1.1,volume=5dB',
  '-c:v', 'libx264',
  '-preset', 'superfast',
  '-crf', '22',
  '-pix_fmt', 'yuv420p',
  '-c:a', 'aac',
  '-b:a', '192k',
  '-ar', '44100',
  outputFile
];

const proc = spawn('ffmpeg', args);
let lastPct = -1;

proc.stderr.on('data', data => {
  const text = data.toString();
  const timeMatch = text.match(/time=(\d+):(\d+):(\d+\.\d+)/);
  if (timeMatch) {
    const hours = parseFloat(timeMatch[1]);
    const mins = parseFloat(timeMatch[2]);
    const secs = parseFloat(timeMatch[3]);
    const currentSec = hours * 3600 + mins * 60 + secs;
    const pct = Math.min(100, Math.floor((currentSec / totalDurationSec) * 100));

    // Log every 5%
    if (pct !== lastPct && pct % 5 === 0) {
      lastPct = pct;
      const speedMatch = text.match(/speed=\s*([\d\.]+x)/);
      const speed = speedMatch ? speedMatch[1] : '';
      console.log(`Progress: ${pct}% (${timeMatch[0]}) | Speed: ${speed}`);
    }
  }
});

proc.on('close', code => {
  if (code === 0) {
    console.log('FFmpeg completed successfully! Output file is ready.');
  } else {
    console.error(`FFmpeg failed with exit code ${code}`);
    process.exit(code);
  }
});

import fs from 'node:fs';
import path from 'node:path';
import { pipeline } from 'node:stream/promises';
import { Readable } from 'node:stream';

const TARGET_DIR = 'D:\\Drama Kingshort\\Perlawanan Supir Truk';
const BASE_URL = 'https://stream.shortlovers.id/dramas/netshort/perlawanan-supir-truk';
const TOTAL_EPS = 33;
const CONCURRENCY = 5;

if (!fs.existsSync(TARGET_DIR)) {
  fs.mkdirSync(TARGET_DIR, { recursive: true });
}

async function downloadEpisode(epNum) {
  const pad = String(epNum).padStart(3, '0');
  const filename = `ep${pad}.mp4`;
  const filePath = path.join(TARGET_DIR, filename);
  const url = `${BASE_URL}/${filename}`;

  // Check if file already exists with non-zero size
  if (fs.existsSync(filePath)) {
    const stat = fs.statSync(filePath);
    if (stat.size > 1000000) {
      console.log(`[SKIPPED] ${filename} already exists (${(stat.size / 1024 / 1024).toFixed(2)} MB)`);
      return;
    }
  }

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      console.log(`[DOWNLOADING] ${filename} from ${url} (attempt ${attempt})...`);
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);

      const fileStream = fs.createWriteStream(filePath);
      await pipeline(Readable.fromWeb(res.body), fileStream);

      const stat = fs.statSync(filePath);
      console.log(`[DONE] ${filename} (${(stat.size / 1024 / 1024).toFixed(2)} MB)`);
      return;
    } catch (err) {
      console.error(`[ERROR] ${filename} attempt ${attempt} failed: ${err.message}`);
      if (attempt === 3) throw err;
      await new Promise(r => setTimeout(r, 1000));
    }
  }
}

async function main() {
  console.log(`Starting download of ${TOTAL_EPS} episodes into "${TARGET_DIR}"...`);
  const queue = Array.from({ length: TOTAL_EPS }, (_, i) => i + 1);

  async function worker() {
    while (queue.length > 0) {
      const epNum = queue.shift();
      await downloadEpisode(epNum);
    }
  }

  const workers = Array.from({ length: CONCURRENCY }, () => worker());
  await Promise.all(workers);
  console.log('All downloads completed successfully!');
}

main().catch(err => {
  console.error('Fatal error in downloader:', err);
  process.exit(1);
});

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// Gunakan node-fetch bawaan Node >= 18 atau module bawaan project
const fetch = require('node-fetch');

const targetDir = 'D:\\Video_Drama';

// Buat direktori jika belum ada
if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
}

// Fungsi untuk mendownload file
async function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(destPath);
    const client = url.startsWith('https') ? https : http;
    client.get(url, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return downloadFile(res.headers.location, destPath).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) {
        return reject(new Error(`Status Code: ${res.statusCode}`));
      }
      res.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(destPath, () => {});
      reject(err);
    });
  });
}

async function main() {
  try {
    console.log("Mencari drama 'Aku Penguasa Abadi' di API...");
    const searchRes = await fetch('https://api.shortlovers.id/api/dramas/search?q=' + encodeURIComponent('Aku Penguasa Abadi'));
    const searchData = await searchRes.json();
    
    const drama = searchData.dramas.find(d => d.title.includes('Aku Penguasa Abadi'));
    if (!drama) {
      console.log("Drama tidak ditemukan!");
      return;
    }

    console.log(`\nKetemu: ${drama.title} (ID: ${drama.id})`);
    
    // Download Cover
    if (drama.coverUrl) {
      // Ambil ekstensi dari URL, default ke .jpg
      let coverExt = path.extname(new URL(drama.coverUrl).pathname);
      if (!coverExt || coverExt.length > 5) coverExt = '.jpg';
      const coverDest = path.join(targetDir, `Cover_${drama.title.replace(/[^a-z0-9]/gi, '_')}${coverExt}`);
      
      console.log(`Mendownload cover ke ${coverDest}...`);
      await downloadFile(drama.coverUrl, coverDest);
      console.log('✅ Cover berhasil didownload.');
    }

    console.log("\nMengambil daftar episode...");
    const epRes = await fetch(`https://api.shortlovers.id/api/dramas/${drama.id}/episodes`);
    const episodes = await epRes.json();

    console.log(`Ditemukan ${episodes.length} episode. Memulai download ke folder: ${targetDir}\n`);

    for (const ep of episodes) {
      const videoUrl = ep.videoUrl || ep.videoUrl540p;
      if (!videoUrl) {
        console.log(`⚠️ Episode ${ep.episodeNumber} tidak memiliki URL video, dilewati.`);
        continue;
      }

      // Abaikan m3u8 sementara (butuh ffmpeg), asumsikan mp4
      if (videoUrl.includes('.m3u8')) {
        console.log(`⚠️ Episode ${ep.episodeNumber} adalah stream m3u8. URL: ${videoUrl}`);
        continue;
      }
      
      const fileName = `Aku_Penguasa_Abadi_Ep_${ep.episodeNumber.toString().padStart(3, '0')}.mp4`;
      const destPath = path.join(targetDir, fileName);
      
      if (fs.existsSync(destPath)) {
        console.log(`⏩ [Episode ${ep.episodeNumber}] Sudah ada, dilewati.`);
        continue;
      }
      
      console.log(`⬇️ [Episode ${ep.episodeNumber}] Mendownload...`);
      try {
        await downloadFile(videoUrl, destPath);
        console.log(`✅ [Episode ${ep.episodeNumber}] Selesai didownload.`);
      } catch (err) {
        console.error(`❌ [Episode ${ep.episodeNumber}] Gagal mendownload: ${err.message}`);
      }
    }
    
    console.log("\n🎉 Semua proses selesai!");

  } catch (err) {
    console.error("Terjadi kesalahan:", err.message);
  }
}

main();

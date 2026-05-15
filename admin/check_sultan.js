const fetch = require('node-fetch');

async function checkEpisode() {
  try {
    console.log("Mencari drama 'Miskin' di API...");
    const searchRes = await fetch('https://api.shortlovers.id/api/dramas/search?q=Miskin');
    const searchData = await searchRes.json();
    
    const drama = searchData.dramas.find(d => d.title.includes('Miskin'));
    if (!drama) {
      console.log("Drama tidak ditemukan!");
      return;
    }

    console.log(`\nKetemu: ${drama.title} (ID: ${drama.id})`);
    
    console.log(`Mengambil daftar episode untuk drama ini...`);
    const epRes = await fetch(`https://api.shortlovers.id/api/dramas/${drama.id}/episodes`);
    const episodes = await epRes.json();
    
    const targetEp = episodes.find(e => e.episodeNumber === 62);
    
    if (targetEp) {
      console.log(`\n--- DATA EPISODE 62 ---`);
      console.log(`Video URL: ${targetEp.videoUrl}`);
      console.log(`Video 540p: ${targetEp.videoUrl540p || 'TIDAK TERSEDIA'}`);
      
      if (targetEp.videoUrl.endsWith('.mp4')) {
        console.log(`\n⚠️ PERINGATAN: Video masih menggunakan format .mp4 utuh, bukan streaming (m3u8). Ini penyebab utama video berat dan macet!`);
      } else if (targetEp.videoUrl.includes('m3u8')) {
        console.log(`\n✅ Format sudah streaming (m3u8).`);
      }
      
      if (!targetEp.videoUrl540p) {
         console.log(`⚠️ PERINGATAN: Resolusi rendah (540p) tidak tersedia. Jika koneksi lambat, video akan sangat macet!`);
      }
      
      console.log(`Host asli:`, new URL(targetEp.videoUrl).hostname);
    } else {
      console.log("Episode 62 tidak ditemukan!");
    }
    
  } catch (err) {
    console.error("Terjadi kesalahan:", err.message);
  }
}

checkEpisode();

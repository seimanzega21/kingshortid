// D:\kingshortid\hybrid_streaming_v2\streamProvider.js
// Ini adalah contoh modul Backend untuk "On-the-fly Fetching"

import axios from 'axios';

/**
 * Fungsi ini dipanggil saat pengguna meminta URL video dari Episode tertentu.
 * @param {Object} drama - Data Drama dari Database (harus punya providerName dan sourceMovieId)
 * @param {Object} episode - Data Episode dari Database (harus punya episodeNumber atau sourceEpisodeId)
 * @returns {Promise<String>} - Mengembalikan Fresh Stream URL (M3U8 / MP4)
 */
export async function getFreshStreamUrl(drama, episode) {
  // 1. Jika video sudah ada di R2, langsung kembalikan URL R2-nya (Skenario Lama)
  if (episode.videoUrl && episode.videoUrl.trim() !== '') {
    return episode.videoUrl;
  }

  // 2. Jika tidak ada di R2, tapi punya providerName, kita ambil secara On-The-Fly!
  if (!drama.providerName || !drama.sourceMovieId) {
    throw new Error('Video tidak ditemukan di R2 dan tidak ada data Provider.');
  }

  const provider = drama.providerName.toLowerCase();
  const movieId = drama.sourceMovieId;
  const epNumber = episode.episodeNumber;

  try {
    let streamUrl = null;

    // --- ROUTER (PENGATUR JALAN) UNTUK 15 PROVIDER ---
    switch (provider) {
      
      case 'melolov3':
      case 'melolov2':
        // Melolo membalas dengan list semua episode
        const meloloRes = await axios.get(`https://vidrama.asia/api/${provider}/multi-video?id=${movieId}&lang=id`, {
          headers: { 'Referer': 'https://vidrama.asia/' }
        });
        const meloloEpisodes = meloloRes.data.episodes;
        // Cari episode yang sesuai (Ingat: index array mulai dari 0)
        const targetMeloloEp = meloloEpisodes.find(ep => ep.index === epNumber) || meloloEpisodes[epNumber - 1];
        streamUrl = targetMeloloEp?.stream_url;
        break;

      case 'dramawavev2':
      case 'dramawave':
        // Dramawave memiliki endpoint stream khusus per episode
        const dwRes = await axios.get(`https://vidrama.asia/api/${provider}?action=stream&id=${movieId}&episode=${epNumber}`, {
          headers: { 'Referer': 'https://vidrama.asia/' }
        });
        streamUrl = dwRes.data.url || dwRes.data.stream_url; // Disesuaikan dengan respon asli API
        break;

      case 'reelshort':
        const rsRes = await axios.get(`https://vidrama.asia/api/reelshort/video?bookId=${movieId}&episode=${epNumber}`, {
          headers: { 'Referer': 'https://vidrama.asia/' }
        });
        streamUrl = rsRes.data.url;
        break;

      // Tambahkan case untuk provider lain (netshortv2, dmboxx, dll) sesuai kebutuhan
      case 'netshortv2':
      case 'dmboxx':
      case 'goodshortv2':
      case 'dotdrama':
      case 'microdrama':
      case 'dramabox':
      case 'idrama':
      case 'flick3':
      case 'shortmax':
      case 'freereels':
      case 'cubetv':
        // Contoh fallback umum (Nanti disesuaikan dengan script python masing-masing)
        const fallbackRes = await axios.get(`https://vidrama.asia/api/${provider}/video?id=${movieId}&episode=${epNumber}`, {
          headers: { 'Referer': 'https://vidrama.asia/' }
        });
        streamUrl = fallbackRes.data.stream_url;
        break;

      default:
        throw new Error(`Provider ${provider} belum didukung oleh Router.`);
    }

    if (!streamUrl) {
      throw new Error('Gagal mendapatkan Fresh URL dari Provider.');
    }

    return streamUrl;

  } catch (error) {
    console.error(`[Streaming Error] Gagal fetch dari ${provider}:`, error.message);
    
    // --- SKENARIO FALLBACK (Circuit Breaker) ---
    // Jika server luar mati, kita coba fallback (meski di atas kita asumsikan videoUrl kosong)
    // Ini berguna jika nanti ada logika R2 sekunder.
    throw new Error('Server sumber sedang gangguan. Silakan coba lagi nanti.');
  }
}

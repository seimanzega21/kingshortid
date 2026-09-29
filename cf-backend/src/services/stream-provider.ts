// src/services/stream-provider.ts

export async function fetchFreshStreamUrl(
    providerName: string,
    sourceMovieId: string,
    episodeNumber: number,
    sourceEpisodeId: string | null = null
): Promise<string | null> {
    const provider = providerName.toLowerCase();
    
    try {
        let streamUrl: string | null = null;
        
        switch (provider) {
            case 'melolov3':
            case 'melolov2': {
                const res = await fetch(`https://vidrama.asia/api/${provider}/multi-video?id=${sourceMovieId}&lang=id`, {
                    headers: { 'Referer': 'https://vidrama.asia/' }
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data: any = await res.json();
                const episodes = data.episodes || [];
                // Find by exact index, or fallback to array index
                const targetEp = episodes.find((ep: any) => ep.index === episodeNumber) || episodes[episodeNumber - 1];
                streamUrl = targetEp?.stream_url || null;
                break;
            }

            case 'dramawavev2':
            case 'dramawave': {
                const res = await fetch(`https://vidrama.asia/api/${provider}?action=stream&id=${sourceMovieId}&episode=${episodeNumber}`, {
                    headers: { 'Referer': 'https://vidrama.asia/' }
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data: any = await res.json();
                streamUrl = data.url || data.stream_url || null;
                break;
            }

            case 'reelshort': {
                const res = await fetch(`https://vidrama.asia/api/reelshort/video?bookId=${sourceMovieId}&episode=${episodeNumber}`, {
                    headers: { 'Referer': 'https://vidrama.asia/' }
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data: any = await res.json();
                streamUrl = data.url || null;
                break;
            }

            default: {
                // Universal fallback for dotdrama, microdrama, dramabox, dmboxx, netshortv2, etc.
                const fallbackRes = await fetch(`https://vidrama.asia/api/${provider}/video?id=${sourceMovieId}&episode=${episodeNumber}`, {
                    headers: { 'Referer': 'https://vidrama.asia/' }
                });
                if (!fallbackRes.ok) throw new Error(`HTTP ${fallbackRes.status}`);
                const data: any = await fallbackRes.json();
                streamUrl = data.stream_url || data.url || null;
                break;
            }
        }
        
        return streamUrl;

    } catch (err) {
        console.error(`[HybridStream] Failed to fetch from ${provider}:`, err);
        return null; // Return null so frontend handles video error (e.g. server down)
    }
}

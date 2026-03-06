/**
 * TypeScript type definitions for scraped data
 */

export interface ScrapedDrama {
    // From GoodShort API
    goodshortId: string;
    title: string;
    synopsis: string;
    coverUrl: string;
    genres: string[];
    language: string;
    episodeCount: number;
    viewCount: number;
    status: string; // COMPLETE, ONGOING

    // From episode data
    episodes: ScrapedEpisode[];
}

export interface ScrapedEpisode {
    goodshortChapterId: number;
    dramaId: string;
    episodeNumber: number;
    title: string;
    duration: number; // in seconds
    thumbnailUrl: string;
    videoUrl720p: string | null;
    videoUrl540p: string | null;
    videoUrl1080p: string | null;
    price: number;
    playCount: number;
}

export interface ScrapeResult {
    success: boolean;
    dramasScraped: number;
    episodesScraped: number;
    errors: string[];
    data: ScrapedDrama[];
}

/**
 * Drama Scraper Module
 * Scrapes drama metadata and episode information from GoodShort API
 */

import { apiClient, GoodShortBook, GoodShortChapter, RecommendListItem } from './api-client';
import { ScrapedDrama, ScrapedEpisode, ScrapeResult } from './types';
import { config } from './config';

// Utility to add delay between requests
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Extract video URL by quality
 */
function getVideoUrlByQuality(chapter: GoodShortChapter, quality: string): string | null {
    const video = chapter.multiVideos?.find(v => v.type === quality);
    return video?.filePath || null;
}

/**
 * Transform GoodShort book data to our ScrapedDrama format
 */
function transformBook(item: RecommendListItem): Omit<ScrapedDrama, 'episodes'> {
    const book = item.book;

    return {
        goodshortId: book.bookId,
        title: book.bookName,
        synopsis: book.introduction || '',
        coverUrl: book.cover || book.bookDetailCover,
        genres: book.labels || [],
        language: book.language || 'BAHASA_INDONESIA',
        episodeCount: book.chapterCount || 0,
        viewCount: book.viewCount || 0,
        status: book.writeStatus || 'COMPLETE',
    };
}

/**
 * Transform GoodShort chapter to our ScrapedEpisode format
 */
function transformChapter(chapter: GoodShortChapter): ScrapedEpisode {
    return {
        goodshortChapterId: chapter.id,
        dramaId: chapter.bookId,
        episodeNumber: chapter.index + 1, // Convert 0-indexed to 1-indexed
        title: `Episode ${chapter.chapterName}`,
        duration: chapter.playTime || 0,
        thumbnailUrl: chapter.image || '',
        videoUrl720p: getVideoUrlByQuality(chapter, '720p'),
        videoUrl540p: getVideoUrlByQuality(chapter, '540p'),
        videoUrl1080p: getVideoUrlByQuality(chapter, '1080p'),
        price: chapter.price || 0,
        playCount: chapter.playCount || 0,
    };
}

/**
 * Scrape drama list from GoodShort
 */
export async function scrapeDramaList(limit: number = 5): Promise<ScrapeResult> {
    const result: ScrapeResult = {
        success: true,
        dramasScraped: 0,
        episodesScraped: 0,
        errors: [],
        data: [],
    };

    try {
        console.log(`\n🎬 Starting GoodShort scraper...`);
        console.log(`📊 Limit: ${limit} dramas\n`);

        // Step 1: Get recommended drama list
        console.log('📡 Fetching drama list...');
        const recommendList = await apiClient.getRecommendList();

        if (!recommendList || recommendList.length === 0) {
            throw new Error('No dramas found in recommend list');
        }

        console.log(`✅ Found ${recommendList.length} dramas\n`);

        // Step 2: Process each drama (up to limit)
        const dramasToProcess = recommendList.slice(0, limit);

        for (let i = 0; i < dramasToProcess.length; i++) {
            const item = dramasToProcess[i];
            const book = item.book;

            console.log(`\n[${i + 1}/${dramasToProcess.length}] Processing: ${book.bookName}`);
            console.log(`   📖 ID: ${book.bookId}`);
            console.log(`   📺 Episodes: ${book.chapterCount}`);

            try {
                // Transform book data
                const drama: ScrapedDrama = {
                    ...transformBook(item),
                    episodes: [],
                };

                // Add first chapter from recommend response
                if (item.chapter) {
                    const firstEpisode = transformChapter(item.chapter);
                    drama.episodes.push(firstEpisode);
                    result.episodesScraped++;
                    console.log(`   ✅ Episode 1 data captured`);
                }

                // Add next chapter if available
                if (item.nextChapter) {
                    const nextEpisode = transformChapter(item.nextChapter as GoodShortChapter);
                    drama.episodes.push(nextEpisode);
                    result.episodesScraped++;
                    console.log(`   ✅ Episode 2 data captured`);
                }

                // Note: To get all episodes, you would need to iterate through
                // all chapter IDs using the /chapter/load endpoint
                // For now, we capture first 2 episodes from recommend response

                result.data.push(drama);
                result.dramasScraped++;

                console.log(`   🎉 Drama scraped successfully!`);

            } catch (error: any) {
                const errorMsg = `Failed to scrape ${book.bookName}: ${error.message}`;
                console.error(`   ❌ ${errorMsg}`);
                result.errors.push(errorMsg);
            }

            // Delay between requests
            if (i < dramasToProcess.length - 1) {
                await delay(config.scraping.requestDelay);
            }
        }

        console.log(`\n${'='.repeat(50)}`);
        console.log(`📊 Scraping Complete!`);
        console.log(`   ✅ Dramas: ${result.dramasScraped}`);
        console.log(`   ✅ Episodes: ${result.episodesScraped}`);
        console.log(`   ❌ Errors: ${result.errors.length}`);
        console.log(`${'='.repeat(50)}\n`);

    } catch (error: any) {
        result.success = false;
        result.errors.push(error.message);
        console.error(`\n❌ Scraping failed: ${error.message}`);
    }

    return result;
}

/**
 * Scrape all episodes for a specific drama
 */
export async function scrapeAllEpisodes(bookId: string, chapterIds: number[]): Promise<ScrapedEpisode[]> {
    const episodes: ScrapedEpisode[] = [];

    // Process in batches to avoid rate limiting
    const batchSize = 10;

    for (let i = 0; i < chapterIds.length; i += batchSize) {
        const batch = chapterIds.slice(i, i + batchSize);

        console.log(`   Loading episodes ${i + 1} to ${Math.min(i + batchSize, chapterIds.length)}...`);

        try {
            const chapters = await apiClient.loadChapters(bookId, batch);

            for (const chapter of chapters) {
                episodes.push(transformChapter(chapter));
            }

            await delay(config.scraping.requestDelay);

        } catch (error: any) {
            console.error(`   ❌ Failed to load batch: ${error.message}`);
        }
    }

    return episodes;
}

export default { scrapeDramaList, scrapeAllEpisodes };

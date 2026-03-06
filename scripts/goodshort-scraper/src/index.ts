/**
 * GoodShort Scraper - Main Entry Point
 * 
 * Usage:
 *   npm run scrape           # Scrape 5 dramas (default)
 *   npm run scrape -- --limit 10  # Scrape 10 dramas
 */

import { scrapeDramaList } from './scraper';
import { saveToJson, saveSqlToFile } from './database';
import { config } from './config';

async function main() {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║           GoodShort Drama Scraper v1.0.0                  ║
║           Based on Reverse-Engineered API                 ║
╚═══════════════════════════════════════════════════════════╝
`);

    // Parse command line arguments
    const args = process.argv.slice(2);
    let limit = config.scraping.dramaLimit;

    const limitArg = args.find(arg => arg.startsWith('--limit'));
    if (limitArg) {
        const limitValue = args[args.indexOf(limitArg) + 1];
        if (limitValue) {
            limit = parseInt(limitValue, 10);
        }
    }

    // Check for auth token
    if (!config.authToken || config.authToken === 'Bearer YOUR_TOKEN_HERE') {
        console.error('❌ Error: GOODSHORT_AUTH_TOKEN not configured!');
        console.error('');
        console.error('Please set your Bearer token in .env file:');
        console.error('1. Copy .env.example to .env');
        console.error('2. Paste your Bearer token from HTTP Toolkit');
        console.error('');
        process.exit(1);
    }

    try {
        // Run scraper
        const result = await scrapeDramaList(limit);

        if (result.success && result.data.length > 0) {
            // Save results to JSON
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            saveToJson(result, `scraped-${timestamp}.json`);

            // Generate SQL import file
            saveSqlToFile(result.data, `import-${timestamp}.sql`);

            // Print sample data
            console.log('\n📋 Sample Drama Data:');
            console.log('─'.repeat(50));

            const sample = result.data[0];
            console.log(`Title: ${sample.title}`);
            console.log(`Genres: ${sample.genres.join(', ')}`);
            console.log(`Episodes: ${sample.episodeCount}`);
            console.log(`Synopsis: ${sample.synopsis.substring(0, 100)}...`);
            console.log(`Cover: ${sample.coverUrl}`);

            if (sample.episodes.length > 0) {
                console.log(`\nFirst Episode Video URL:`);
                console.log(`  720p: ${sample.episodes[0].videoUrl720p?.substring(0, 80)}...`);
            }
        }

    } catch (error: any) {
        console.error(`\n❌ Fatal error: ${error.message}`);
        process.exit(1);
    }
}

// Run main function
main().catch(console.error);

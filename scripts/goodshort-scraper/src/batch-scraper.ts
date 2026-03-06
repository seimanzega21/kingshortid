/**
 * Batch Scraper - Scrape multiple dramas with complete metadata
 * 
 * Usage:
 *   npm run batch-scrape
 *   
 * This will scrape the dramas listed in batch-list.json
 */

import fs from 'fs';
import path from 'path';
import { scrapeDrama } from './complete-scraper';

interface BatchConfig {
    dramas: Array<{
        bookId: string;
        priority?: number;
    }>;
}

const BATCH_LIST_FILE = path.join(__dirname, '../batch-list.json');
const OUTPUT_DIR = path.join(__dirname, '../output');

async function wait(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function batchScrape() {
    console.log('\n' + '='.repeat(60));
    console.log('🎬 GoodShort Batch Scraper');
    console.log('='.repeat(60) + '\n');

    // Load batch list
    if (!fs.existsSync(BATCH_LIST_FILE)) {
        console.log('❌ batch-list.json not found!');
        console.log('\nCreating sample batch-list.json...\n');

        const sample: BatchConfig = {
            dramas: [
                { bookId: '31000991502', priority: 1 },
                { bookId: '31001051678', priority: 2 },
                { bookId: '31001241698', priority: 3 }
            ]
        };

        fs.writeFileSync(
            BATCH_LIST_FILE,
            JSON.stringify(sample, null, 2)
        );

        console.log('✅ Created batch-list.json');
        console.log('   Edit this file to add drama IDs, then run again.\n');
        return;
    }

    const config: BatchConfig = JSON.parse(
        fs.readFileSync(BATCH_LIST_FILE, 'utf-8')
    );

    const dramas = config.dramas.sort((a, b) =>
        (a.priority || 999) - (b.priority || 999)
    );

    console.log(`📋 Found ${dramas.length} dramas to scrape\n`);

    const results = {
        success: [] as string[],
        failed: [] as string[],
        total: dramas.length,
        startTime: new Date().toISOString(),
        endTime: ''
    };

    for (let i = 0; i < dramas.length; i++) {
        const drama = dramas[i];
        console.log(`\n[${i + 1}/${dramas.length}] Starting: ${drama.bookId}`);

        try {
            const result = await scrapeDrama(drama.bookId);

            if (result) {
                results.success.push(drama.bookId);
                console.log(`✅ Success: ${result.metadata.title}`);
            } else {
                results.failed.push(drama.bookId);
                console.log(`❌ Failed: ${drama.bookId}`);
            }
        } catch (error: any) {
            results.failed.push(drama.bookId);
            console.log(`❌ Error: ${error.message}`);
        }

        // Wait between dramas to avoid rate limiting
        if (i < dramas.length - 1) {
            console.log('\n⏳ Waiting 5 seconds before next drama...');
            await wait(5000);
        }
    }

    // Save results
    results.endTime = new Date().toISOString();

    const resultsFile = path.join(OUTPUT_DIR, 'batch-results.json');
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));

    // Print summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 BATCH SCRAPING COMPLETE');
    console.log('='.repeat(60));
    console.log(`✅ Success: ${results.success.length}/${results.total}`);
    console.log(`❌ Failed:  ${results.failed.length}/${results.total}`);

    if (results.failed.length > 0) {
        console.log('\nFailed dramas:');
        results.failed.forEach(id => console.log(`  - ${id}`));
    }

    console.log(`\nResults saved: ${resultsFile}`);
    console.log('='.repeat(60) + '\n');
}

// Run if called directly
if (require.main === module) {
    batchScrape()
        .then(() => process.exit(0))
        .catch(error => {
            console.error('❌ Batch scraping failed:', error);
            process.exit(1);
        });
}

export { batchScrape };

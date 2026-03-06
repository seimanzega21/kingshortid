/**
 * Import GoodShort Content to KingShortID Database (Direct SQL)
 * 
 * Reads R2 upload results and imports dramas/episodes to PostgreSQL
 * Uses direct SQL queries instead of Prisma
 * 
 * Usage: npx ts-node src/import-to-database.ts
 */

import { Client } from 'pg';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config();

interface R2UploadResult {
    uploadedAt: string;
    totalDramas: number;
    totalEpisodes: number;
    dramas: {
        bookId: string;
        coverUrl: string | null;
        episodes: {
            chapterId: string;
            videoUrl: string;
            fileSize: number;
        }[];
    }[];
}

interface CapturedData {
    dramas: {
        [bookId: string]: {
            bookId: string;
            title: string;
            cover: string | null;
            episodes: any;
        }
    };
    lastUpdate: string;
}

/**
 * Import a single drama
 */
async function importDrama(
    client: Client,
    bookId: string,
    coverUrl: string | null,
    episodes: { chapterId: string; videoUrl: string; fileSize: number }[],
    capturedData: CapturedData
) {
    const capturedDrama = capturedData.dramas[bookId];
    const title = capturedDrama?.title || `Drama ${bookId}`;

    console.log(`\n📺 Importing: ${title} (${bookId})`);

    // Check if drama already exists
    const existingDrama = await client.query(
        'SELECT id FROM "Drama" WHERE "externalId" = $1',
        [bookId]
    );

    let dramaId: number;

    if (existingDrama.rows.length > 0) {
        dramaId = existingDrama.rows[0].id;
        console.log(`  ⏭️  Drama already exists (ID: ${dramaId}), updating...`);

        // Update existing drama
        await client.query(
            `UPDATE "Drama" 
             SET "coverUrl" = COALESCE($1, "coverUrl"), 
                 "episodeCount" = $2,
                 "updatedAt" = NOW()
             WHERE id = $3`,
            [coverUrl, episodes.length, dramaId]
        );
    } else {
        // Create new drama  
        const result = await client.query(
            `INSERT INTO "Drama" (
                title, synopsis, "coverUrl", genres, 
                "episodeCount", status, "externalId", 
                "createdAt", "updatedAt"
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            RETURNING id`,
            [
                title,
                'Imported from GoodShort',
                coverUrl || '',
                ['Drama', 'Romance'],
                episodes.length,
                'COMPLETE',
                bookId
            ]
        );

        dramaId = result.rows[0].id;
        console.log(`  ✅ Created drama (ID: ${dramaId})`);
    }

    // Import episodes
    let importedCount = 0;
    let skippedCount = 0;

    for (let i = 0; i < episodes.length; i++) {
        const episode = episodes[i];
        const episodeNumber = i + 1;

        // Check if episode already exists
        const existingEpisode = await client.query(
            'SELECT id FROM "Episode" WHERE "dramaId" = $1 AND "externalId" = $2',
            [dramaId, episode.chapterId]
        );

        if (existingEpisode.rows.length > 0) {
            skippedCount++;
            continue;
        }

        await client.query(
            `INSERT INTO "Episode" (
                "dramaId", "episodeNumber", title, 
                "videoUrl", "thumbnailUrl", duration,
                "externalId", "createdAt", "updatedAt"
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())`,
            [
                dramaId,
                episodeNumber,
                `Episode ${episodeNumber}`,
                episode.videoUrl,
                coverUrl || '',
                120, // Default 2 minutes
                episode.chapterId
            ]
        );

        importedCount++;
    }

    console.log(`  ✅ Imported ${importedCount} episodes (${skippedCount} already existed)`);

    return {
        dramaId,
        title,
        episodesImported: importedCount,
        episodesSkipped: skippedCount,
    };
}

/**
 * Main import function
 */
async function main() {
    console.log('\n' + '='.repeat(60));
    console.log('GoodShort → KingShortID Database Import');
    console.log('='.repeat(60));

    // Check for R2 upload results
    const r2ResultsPath = path.join(__dirname, '..', 'r2-upload-results.json');
    if (!fs.existsSync(r2ResultsPath)) {
        console.error('\n❌ r2-upload-results.json not found');
        console.error('   Run upload-to-r2.ts first to upload videos to R2');
        process.exit(1);
    }

    // Load R2 results
    const r2Results: R2UploadResult = JSON.parse(fs.readFileSync(r2ResultsPath, 'utf-8'));

    console.log(`\n📦 R2 Upload Results:`);
    console.log(`   Uploaded: ${r2Results.uploadedAt}`);
    console.log(`   Dramas: ${r2Results.totalDramas}`);
    console.log(`   Episodes: ${r2Results.totalEpisodes}`);

    // Load captured episode metadata (for titles)
    const capturedDataPath = path.join(__dirname, '..', 'captured-episodes.json');
    let capturedData: CapturedData = { dramas: {}, lastUpdate: '' };

    if (fs.existsSync(capturedDataPath)) {
        capturedData = JSON.parse(fs.readFileSync(capturedDataPath, 'utf-8'));
        console.log(`\n📋 Loaded metadata from captured-episodes.json`);
    } else {
        console.log(`\n⚠️  captured-episodes.json not found, using generic titles`);
    }

    // Connect to database
    const client = new Client({
        connectionString: process.env.DATABASE_URL,
    });

    try {
        await client.connect();
        console.log(`\n✅ Connected to database`);
    } catch (error: any) {
        console.error('\n❌ Failed to connect to database:', error.message);
        console.error('   Check DATABASE_URL in .env');
        process.exit(1);
    }

    // Import all dramas
    const importResults = [];

    for (const drama of r2Results.dramas) {
        // Skip empty dramas (like 31001250379_634143 folder with no episodes)
        if (drama.episodes.length === 0) {
            console.log(`\n⏭️  Skipping ${drama.bookId} (no episodes)`);
            continue;
        }

        try {
            const result = await importDrama(
                client,
                drama.bookId,
                drama.coverUrl,
                drama.episodes,
                capturedData
            );
            importResults.push(result);
        } catch (error: any) {
            console.error(`\n❌ Failed to import drama ${drama.bookId}:`, error.message);
        }
    }

    await client.end();

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('✅ Import Complete!');
    console.log('='.repeat(60));
    console.log(`Dramas Imported: ${importResults.length}`);
    console.log(`Episodes Imported: ${importResults.reduce((sum, r) => sum + r.episodesImported, 0)}`);
    console.log(`Episodes Skipped: ${importResults.reduce((sum, r) => sum + r.episodesSkipped, 0)}`);

    console.log('\n📋 Imported Dramas:');
    for (const result of importResults) {
        console.log(`   • ${result.title} (ID: ${result.dramaId}) - ${result.episodesImported} episodes`);
    }

    console.log('\n' + '='.repeat(60));
    console.log('Next: Test in KingShortID mobile app!');
    console.log('='.repeat(60) + '\n');
}

main().catch(console.error);

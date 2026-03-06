/**
 * Import GoodShort Content to KingShortID Database
 * 
 * Reads R2 upload results and imports dramas/episodes to PostgreSQL
 * 
 * Usage: npx ts-node src/import-to-kingshortid.ts
 */

import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config();

const prisma = new PrismaClient();

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

interface CapturedEpisode {
    chapterId: string;
    token: string;
    videoId: string;
    resolution: string;
}

interface CapturedDrama {
    bookId: string;
    title: string;
    cover: string | null;
    episodes: { [chapterId: string]: CapturedEpisode };
}

interface CapturedData {
    dramas: { [bookId: string]: CapturedDrama };
    lastUpdate: string;
}

/**
 * Import a single drama
 */
async function importDrama(
    bookId: string,
    coverUrl: string | null,
    episodes: { chapterId: string; videoUrl: string; fileSize: number }[],
    capturedData: CapturedData
) {
    const capturedDrama = capturedData.dramas[bookId];
    const title = capturedDrama?.title || `Drama ${bookId}`;

    console.log(`\n📺 Importing: ${title} (${bookId})`);

    // Check if drama already exists
    let drama = await prisma.drama.findFirst({
        where: { externalId: bookId },
    });

    if (drama) {
        console.log(`  ⏭️  Drama already exists (ID: ${drama.id}), updating...`);

        // Update existing drama
        drama = await prisma.drama.update({
            where: { id: drama.id },
            data: {
                coverUrl: coverUrl || drama.coverUrl,
                episodeCount: episodes.length,
            },
        });
    } else {
        // Create new drama
        drama = await prisma.drama.create({
            data: {
                title,
                synopsis: 'Imported from GoodShort',
                coverUrl: coverUrl || '',
                genres: ['Drama', 'Romance'],
                episodeCount: episodes.length,
                status: 'COMPLETE',
                externalId: bookId,
            },
        });

        console.log(`  ✅ Created drama (ID: ${drama.id})`);
    }

    // Import episodes
    let importedCount = 0;
    let skippedCount = 0;

    for (let i = 0; i < episodes.length; i++) {
        const episode = episodes[i];
        const episodeNumber = i + 1;

        // Check if episode already exists
        const existingEpisode = await prisma.episode.findFirst({
            where: {
                dramaId: drama.id,
                externalId: episode.chapterId,
            },
        });

        if (existingEpisode) {
            skippedCount++;
            continue;
        }

        await prisma.episode.create({
            data: {
                dramaId: drama.id,
                episodeNumber,
                title: `Episode ${episodeNumber}`,
                videoUrl: episode.videoUrl,
                thumbnailUrl: coverUrl || '',
                duration: 120, // Default 2 minutes (can update later if we get real duration)
                externalId: episode.chapterId,
            },
        });

        importedCount++;
    }

    console.log(`  ✅ Imported ${importedCount} episodes (${skippedCount} already existed)`);

    return {
        dramaId: drama.id,
        title: drama.title,
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

    // Test database connection
    try {
        await prisma.$connect();
        console.log(`\n✅ Connected to database`);
    } catch (error) {
        console.error('\n❌ Failed to connect to database');
        console.error('   Check DATABASE_URL in .env');
        process.exit(1);
    }

    // Import all dramas
    const importResults = [];

    for (const drama of r2Results.dramas) {
        try {
            const result = await importDrama(
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

    await prisma.$disconnect();

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

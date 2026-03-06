/**
 * Delete drama permanently from DB + R2
 * Usage: node delete_drama.js "Misi Cinta"
 */
const { PrismaClient } = require('@prisma/client');
const { S3Client, ListObjectsV2Command, DeleteObjectsCommand } = require('@aws-sdk/client-s3');
require('dotenv').config();

const p = new PrismaClient();
const s3 = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
    },
});
const BUCKET = process.env.R2_BUCKET_NAME;

async function deleteR2Folder(prefix) {
    let deleted = 0;
    let continuationToken;

    do {
        const list = await s3.send(new ListObjectsV2Command({
            Bucket: BUCKET,
            Prefix: prefix,
            MaxKeys: 1000,
            ContinuationToken: continuationToken,
        }));

        const objects = list.Contents || [];
        if (objects.length === 0) break;

        await s3.send(new DeleteObjectsCommand({
            Bucket: BUCKET,
            Delete: { Objects: objects.map(o => ({ Key: o.Key })) },
        }));

        deleted += objects.length;
        continuationToken = list.NextContinuationToken;
    } while (continuationToken);

    return deleted;
}

async function main() {
    const search = process.argv[2] || 'Misi Cinta';

    const drama = await p.drama.findFirst({
        where: { title: { contains: search } },
        select: { id: true, title: true, totalEpisodes: true, cover: true }
    });

    if (!drama) {
        console.log('Drama not found:', search);
        process.exit(1);
    }

    console.log(`\n🎯 Found: "${drama.title}" (${drama.totalEpisodes} eps)`);
    console.log(`   ID: ${drama.id}`);
    console.log(`   Cover: ${drama.cover}`);

    // Count episodes in DB
    const epCount = await p.episode.count({ where: { dramaId: drama.id } });
    console.log(`   Episodes in DB: ${epCount}`);

    // 1. Delete episodes from DB
    const delEps = await p.episode.deleteMany({ where: { dramaId: drama.id } });
    console.log(`\n✅ Deleted ${delEps.count} episodes from DB`);

    // 2. Delete drama from DB
    await p.drama.delete({ where: { id: drama.id } });
    console.log(`✅ Deleted drama from DB`);

    // 3. Delete from R2 — try common prefixes
    const slugGuess = drama.title.toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, '-');

    const prefixes = [
        `melolo/${slugGuess}/`,
        `vidrama/${slugGuess}/`,
    ];

    for (const prefix of prefixes) {
        const count = await deleteR2Folder(prefix);
        if (count > 0) {
            console.log(`✅ Deleted ${count} files from R2: ${prefix}`);
        } else {
            console.log(`   No files in R2: ${prefix}`);
        }
    }

    console.log(`\n🏁 Drama "${drama.title}" permanently deleted!`);
    await p.$disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });

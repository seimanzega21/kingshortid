/**
 * Test API with captured Frida headers
 * Run: npx ts-node src/test-api.ts
 */

import { apiClient } from './api-client';

async function testHomeIndex() {
    console.log('\n=== Testing home/index API ===\n');

    try {
        const result = await apiClient.getHomeIndex(1, 12);
        console.log('Status:', result.status);
        console.log('Message:', result.message);
        console.log('Success:', result.success);

        if (result.data) {
            console.log('\n--- Drama List ---');
            const dramas = result.data.recommentList || result.data.list || [];
            console.log(`Found ${dramas.length} dramas\n`);

            dramas.slice(0, 5).forEach((item: any, i: number) => {
                const book = item.book || item;
                console.log(`${i + 1}. ${book.bookName || book.name}`);
                console.log(`   ID: ${book.bookId}`);
                console.log(`   Episodes: ${book.chapterCount}`);
                console.log(`   Cover: ${book.cover}`);
                console.log('');
            });
        }

        return result;
    } catch (error: any) {
        console.error('Error:', error.response?.status, error.response?.data || error.message);
        return null;
    }
}

async function testChapterList(bookId: string) {
    console.log(`\n=== Testing chapter/list API for book ${bookId} ===\n`);

    try {
        const result = await apiClient.getChapterList(bookId, 500);
        console.log('Status:', result.status);
        console.log('Message:', result.message);
        console.log('Success:', result.success);

        if (result.data) {
            const chapters = result.data.list || [];
            console.log(`\nFound ${chapters.length} chapters\n`);

            chapters.slice(0, 5).forEach((chapter: any, i: number) => {
                console.log(`${i + 1}. Chapter ${chapter.chapterName}`);
                console.log(`   ID: ${chapter.id}`);
                console.log(`   Play Time: ${chapter.playTime}s`);
                console.log(`   CDN: ${chapter.cdn?.substring(0, 80)}...`);
                console.log('');
            });
        }

        return result;
    } catch (error: any) {
        console.error('Error:', error.response?.status, error.response?.data || error.message);
        return null;
    }
}

async function testReaderInit(bookId: string) {
    console.log(`\n=== Testing reader/init API for book ${bookId} ===\n`);

    try {
        const result = await apiClient.getReaderInit(bookId);
        console.log('Status:', result.status);
        console.log('Message:', result.message);
        console.log('Success:', result.success);

        if (result.data) {
            console.log('\n--- Reader Data ---');
            console.log('Book Info:', JSON.stringify(result.data.book, null, 2).substring(0, 500));
        }

        return result;
    } catch (error: any) {
        console.error('Error:', error.response?.status, error.response?.data || error.message);
        return null;
    }
}

async function main() {
    console.log('========================================');
    console.log('GoodShort API Test with Frida Headers');
    console.log('========================================');
    console.log('\nAvailable endpoints:', apiClient.getAvailableEndpoints());

    // Test 1: Home Index
    const homeResult = await testHomeIndex();

    // If we got dramas, test chapter list with first book
    if (homeResult?.data) {
        const dramas = homeResult.data.recommentList || homeResult.data.list || [];
        if (dramas.length > 0) {
            const firstBook = dramas[0].book || dramas[0];
            const bookId = firstBook.bookId;

            // Test 2: Chapter List
            await testChapterList(bookId);

            // Test 3: Reader Init
            await testReaderInit(bookId);
        }
    }

    console.log('\n========================================');
    console.log('Test Complete');
    console.log('========================================');
}

main().catch(console.error);

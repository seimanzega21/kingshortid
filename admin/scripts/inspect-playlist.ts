import { ListObjectsV2Command, GetObjectCommand } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';

async function inspectPlaylist() {
    const dramaFolder = 'si_kembar_lima_bantu_ayah_kejar_ibu/';
    console.log(`🔍 Listing contents of '${dramaFolder}'...`);

    try {
        const response = await r2Client.send(new ListObjectsV2Command({
            Bucket: R2_BUCKET,
            Prefix: dramaFolder
        }));

        const items = response.Contents || [];
        items.slice(0, 10).forEach(c => console.log(c.Key));

        // Try to find the playlist
        const playlistItem = items.find(i => i.Key?.endsWith('playlist.m3u8'));

        if (playlistItem && playlistItem.Key) {
            console.log(`\n📄 Found Playlist: ${playlistItem.Key}`);
            console.log('Downloading content...');

            const getRes = await r2Client.send(new GetObjectCommand({
                Bucket: R2_BUCKET,
                Key: playlistItem.Key
            }));

            const str = await getRes.Body?.transformToString();
            console.log('\n--- PLAYLIST START ---');
            console.log(str);
            console.log('--- PLAYLIST END ---');
        } else {
            console.log('❌ No playlist.m3u8 found in first batch');
        }

    } catch (error: any) {
        console.error('Error:', error.message);
    }
}

inspectPlaylist();

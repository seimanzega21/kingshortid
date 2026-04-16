import { sql, like } from 'drizzle-orm';
import { episodes } from './src/db/schema';
import { getDb } from './src/db';
import { writeFileSync } from 'fs';

async function main() {
    console.log("Connecting to Supabase production DB...");
    const db = getDb(process.env.SUPABASE_URL as string, process.env.SUPABASE_DB_PASSWORD as string);
    
    console.log("Finding episodes with .m3u8...");
    // Find episodes where videoUrl contains .m3u8 OR videoUrl540p contains .m3u8
    const rawEpisodes = await db.select({
        id: episodes.id,
        dramaId: episodes.dramaId,
        episodeNumber: episodes.episodeNumber,
        videoUrl: episodes.videoUrl,
        videoUrl540p: episodes.videoUrl540p
    }).from(episodes)
      .where(like(episodes.videoUrl, '%m3u8%'));
      
    console.log(`Found ${rawEpisodes.length} episodes with m3u8!`);
    
    writeFileSync('c:/tmp/m3u8_episodes.json', JSON.stringify(rawEpisodes, null, 2));
    console.log("Saved to c:/tmp/m3u8_episodes.json");
    process.exit(0);
}

main().catch(console.error);

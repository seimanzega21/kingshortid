import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { dramas, episodes } from './src/db/schema';
import { eq } from 'drizzle-orm';
import dotenv from 'dotenv';

dotenv.config({ path: '.env.production' });

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error("DATABASE_URL is missing");
  process.exit(1);
}

const client = postgres(connectionString);
const db = drizzle(client);

async function main() {
  const dramaId = 'yzj2ccebx7ndri7wnysj8ws4';

  const dramaData = await db.select().from(dramas).where(eq(dramas.id, dramaId));
  console.log('Drama:', JSON.stringify(dramaData[0], null, 2));

  const episodeData = await db.select().from(episodes).where(eq(episodes.dramaId, dramaId));
  console.log(`\nEpisodes count: ${episodeData.length}`);
  
  // Sort episodes
  episodeData.sort((a, b) => a.episodeNumber - b.episodeNumber);
  console.log('Episodes:', JSON.stringify(episodeData.map(e => ({ num: e.episodeNumber, url: e.videoUrl })), null, 2));

  process.exit(0);
}

main().catch(console.error);

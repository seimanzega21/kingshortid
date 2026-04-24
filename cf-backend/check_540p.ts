import { getDb } from './src/db';
import { episodes } from './src/db/schema';
import { isNotNull, count } from 'drizzle-orm';
import dotenv from 'dotenv';

dotenv.config();

async function main() {
    try {
        const db = getDb(process.env.SUPABASE_URL || '', process.env.SUPABASE_DB_PASSWORD || '');
        const total = await db.select({ count: count() }).from(episodes);
        const with540p = await db.select({ count: count() }).from(episodes).where(isNotNull(episodes.videoUrl540p));
        console.log(`Total episodes: ${total[0].count}`);
        console.log(`Episodes with 540p: ${with540p[0].count}`);
    } catch (e) {
        console.error(e);
    }
    process.exit(0);
}
main();

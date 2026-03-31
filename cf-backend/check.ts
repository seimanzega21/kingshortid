
import { getDb } from './src/db/index';
import { episodes } from './src/db/schema';
import { count, isNotNull, and, eq } from 'drizzle-orm';
import * as dotenv from 'dotenv';
dotenv.config({ path: '.env.production' });

async function check() {
  const db = getDb(process.env.SUPABASE_URL, process.env.SUPABASE_DB_PASSWORD);
  try {
      const [{ count: total }] = await db.select({ count: count() }).from(episodes).where(eq(episodes.isActive, true));
      const [{ count: p540 }] = await db.select({ count: count() }).from(episodes).where(and(eq(episodes.isActive, true), isNotNull(episodes.videoUrl540p)));
      console.log('TOTAL ACTIVE EPISODES: ' + total);
      console.log('EPISODES WITH 540p: ' + p540);
      process.exit(0);
  } catch (e) {
      console.error(e);
      process.exit(1);
  }
}
check();


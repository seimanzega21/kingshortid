const { initDb } = require('./src/db/index.js');
const { count, isNotNull, and, eq } = require('drizzle-orm');
const schema = require('./src/db/schema.js');
require('dotenv').config({ path: '.env.production' });

async function check() {
  const db = initDb(process.env.SUPABASE_URL, process.env.SUPABASE_DB_PASSWORD);
  
  // Total active episodes
  const totalResult = await db.select({ count: count() })
    .from(schema.episodes)
    .where(eq(schema.episodes.isActive, true));
    
  // Active episodes with 540p
  const p540Result = await db.select({ count: count() })
    .from(schema.episodes)
    .where(and(
      eq(schema.episodes.isActive, true),
      isNotNull(schema.episodes.videoUrl540p)
    ));
    
  console.log(TOTAL ACTIVE EPISODES: );
  console.log(EPISODES WITH 540p: );
  
  process.exit(0);
}

check().catch(console.error);

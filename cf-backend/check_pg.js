
const { Client } = require('pg');
require('dotenv').config({ path: '.env.production' });

async function run() {
  const client = new Client({ connectionString: process.env.SUPABASE_URL });
  await client.connect();
  
  const total = await client.query('SELECT COUNT(*) FROM episodes WHERE is_active = true');
  const p540 = await client.query('SELECT COUNT(*) FROM episodes WHERE is_active = true AND video_url_540p IS NOT NULL');
  
  console.log('TOTAL_ACTIVE: ' + total.rows[0].count);
  console.log('HAS_540P: ' + p540.rows[0].count);
  
  await client.end();
}
run().catch(console.error);


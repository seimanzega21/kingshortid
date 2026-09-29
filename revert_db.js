const { Client } = require('pg');
const client = new Client({
  connectionString: 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres'
});

async function run() {
  await client.connect();
  const res = await client.query("UPDATE episodes SET video_url = NULL WHERE video_url = ''");
  console.log('Restored ' + res.rowCount + ' episodes from empty string to NULL.');
  await client.end();
}
run().catch(console.error);

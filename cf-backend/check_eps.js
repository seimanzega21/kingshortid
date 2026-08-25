const { Client } = require('pg');
const client = new Client({ connectionString: 'postgresql://supabase_admin:SUPABASE_DB_PASSWORD@supabase-db-og8gwooogk480gcws0o84ssc:5432/postgres' });
async function run() {
  await client.connect();
  const res = await client.query('SELECT "episodeNumber" FROM "Episode" WHERE "dramaId" = $1 ORDER BY "episodeNumber" ASC', ['p3eufhwku6lgj80ee9i0kafm']);
  const nums = res.rows.map(r => r.episodeNumber);
  console.log('Total:', nums.length);
  if(nums.length > 0) {
      let missing = [];
      for(let i=1; i<=nums[nums.length-1]; i++) {
          if(!nums.includes(i)) missing.push(i);
      }
      console.log('Missing:', missing);
  }
  await client.end();
}
run();

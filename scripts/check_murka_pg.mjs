import pg from 'pg';

const { Client } = pg;
const client = new Client({
  connectionString: 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@supabase-db-og8gwooogk480gcws0o84ssc:5432/postgres'
});

async function run() {
  try {
    await client.connect();
    const res = await client.query("SELECT id, title, total_episodes FROM dramas WHERE title ILIKE '%murka%'");
    console.log("Dramas:", res.rows);
    
    if (res.rows.length > 0) {
      const dramaId = res.rows[0].id;
      const eps = await client.query("SELECT id, episode_number, video_url FROM episodes WHERE drama_id = $1 ORDER BY episode_number ASC LIMIT 5", [dramaId]);
      console.log("Episodes sample:", eps.rows);
    }
  } catch (e) {
    console.error("DB Error:", e);
  } finally {
    await client.end();
  }
}

run();

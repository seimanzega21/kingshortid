import pg from 'pg';

const { Client } = pg;
const client = new Client({
  connectionString: 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres'
});

async function run() {
  try {
    console.log("Menghubungkan ke database...");
    await client.connect();
    
    const slug = 'dua-kuasa-menjadi-satu';
    const r2_cover = `https://stream.shortlovers.id/netshortv2/${slug}/cover.webp`;
    
    const res = await client.query("UPDATE dramas SET cover = $1 WHERE title ILIKE '%Dua Kuasa Menjadi Satu%' RETURNING id, title, cover", [r2_cover]);
    
    if (res.rows.length > 0) {
      console.log("BERHASIL memperbaiki cover URL!");
      console.log("Drama:", res.rows[0].title);
      console.log("New Cover:", res.rows[0].cover);
    } else {
      console.log("Drama tidak ditemukan di DB.");
    }
  } catch (e) {
    console.error("DB Error:", e);
  } finally {
    await client.end();
  }
}

run();

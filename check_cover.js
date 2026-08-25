const { Client } = require('pg');

async function main() {
  const client = new Client({
    connectionString: "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:5435/postgres"
  });
  
  try {
    await client.connect();
    const res = await client.query(`SELECT id, title, slug, cover FROM dramas WHERE slug = 'wzry014zaekel7w7s4ujqwd4' LIMIT 1`);
    console.log("Result:", res.rows);
  } catch (err) {
    console.error("Error:", err);
  } finally {
    await client.end();
  }
}

main();

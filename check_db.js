
const { Client } = require('pg');
const client = new Client({
  connectionString: 'postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:5435/postgres'
});
async function run() {
  await client.connect();
  const res = await client.query('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\'');
  console.log(res.rows.map(r => r.table_name));
  await client.end();
}
run();


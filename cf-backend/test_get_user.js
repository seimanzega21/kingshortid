const postgres = require('postgres');
const sql = postgres('postgresql://postgres:ksh0rtl0v3rs2026!@141.11.160.187:5432/postgres');
sql`select id from users limit 1`.then(r => {
    console.log(r[0].id);
    process.exit(0);
}).catch(console.error);

import pg from 'pg';
const { Client } = pg;

async function debugDashboard() {
    const supabaseUrl = "http://supabasekong-og8gwooogk480gcws0o84ssc.141.11.160.187.sslip.io";
    const dbPassword = "GoZViiH1AXLl73BqLdKDtpeGgwUzfW64";
    
    // Manual build
    const host = "141.11.160.187";
    const connectionString = `postgresql://postgres:${dbPassword}@${host}:5432/postgres`;

    console.log("Connecting to:", connectionString.replace(dbPassword, "****"));
    const client = new Client({
        connectionString: connectionString
    });

    try {
        await client.connect();
        console.log("Connected to DB.");

        const res = await client.query(`SELECT COUNT(*) FROM users`);
        console.log("Users count:", res.rows[0].count);
    } catch (e) {
        console.error("Query failed:", e.message);
    } finally {
        await client.end();
    }
}

debugDashboard();

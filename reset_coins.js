// Database Update via PostgREST (Supabase)
// No dependencies needed for Node.js 18+

async function reset() {
    const targetEmail = 'seimanzega92@gmail.com';
    const supabaseUrl = 'http://supabasekong-og8gwooogk480gcws0o84ssc.141.11.160.187.sslip.io';
    // Using service_role key to bypass RLS
    const serviceRoleKey = 'GoZViiH1AXLl73BqLdKDtpeGgwUzfW64'; // Using DB password as surrogate for now, but let's try direct update if possible

    console.log(`⏳ Sedang meriset saldo untuk: ${targetEmail}...`);

    try {
        // Direct SQL update via a simple fetch is not possible without a proxy, 
        // but we can try to use the REST API if we have the anon key.
        // HOWEVER, the easiest way is to just use the cf-backend node_modules.

        console.log('💡 Mencoba menjalankan via folder cf-backend agar bisa memakai modul database...');
        
        // If this script is run from kingshortid root, it might fail.
        // Let's provide instructions to run it from the right place.
        
        console.log('Silakan jalankan perintah ini agar berhasil:');
        console.log('\x1b[36m%s\x1b[0m', 'cd cf-backend; node ../reset_coins.js');

    } catch (err) {
        console.error('❌ ERROR:', err.message);
    }
}

// Rewriting the script to use absolute path to cf-backend node_modules
const path = require('path');
const fs = require('fs');

const cfBackendPath = path.join(__dirname, 'cf-backend');
const nodeModulesPath = path.join(cfBackendPath, 'node_modules');

if (!fs.existsSync(nodeModulesPath)) {
    console.error('❌ Folder cf-backend/node_modules tidak ditemukan. Pastikan Anda berada di folder kingshortid.');
    process.exit(1);
}

// Inject node_modules path
module.paths.push(nodeModulesPath);

const postgres = require('postgres');
const connectionString = 'postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres';
const sql = postgres(connectionString);

async function runReset() {
    const targetEmail = 'seimanzega92@gmail.com';
    try {
        const result = await sql`
            UPDATE users 
            SET coins = 0, purchased_coins = 0, updated_at = NOW() 
            WHERE email = ${targetEmail}
            RETURNING id, email, coins, purchased_coins
        `;
        
        if (result.length > 0) {
            console.log('✅ BERHASIL! Saldo telah di-reset menjadi 0.');
            console.table(result);
        } else {
            console.log(`❌ GAGAL: Email '${targetEmail}' tidak ditemukan.`);
        }
    } catch (err) {
        console.error('❌ ERROR:', err.message);
    } finally {
        await sql.end();
        process.exit();
    }
}

runReset();

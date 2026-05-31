const path = require('path');
const fs = require('fs');

const cfBackendPath = path.join(__dirname, '..', 'cf-backend');
const nodeModulesPath = path.join(cfBackendPath, 'node_modules');

if (!fs.existsSync(nodeModulesPath)) {
    console.error('❌ Folder cf-backend/node_modules tidak ditemukan.');
    process.exit(1);
}

module.paths.push(nodeModulesPath);

const jose = require('jose');

const JWT_SECRET = 'MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13';
const key = new TextEncoder().encode(JWT_SECRET);

async function generateToken(payload) {
    return new jose.SignJWT(payload)
        .setProtectedHeader({ alg: 'HS256' })
        .setExpirationTime('7d')
        .sign(key);
}

async function test() {
    const payload = {
        id: 'p5ntsk0nv4a0c2aqyxjdwl7y', // seimanzega92@gmail.com
        role: 'user'
    };
    
    console.log('Generating token...');
    const token = await generateToken(payload);
    console.log('Token:', token);
    
    const url = 'https://api.shortlovers.id/api/rewards/watch-video';
    console.log(`Sending POST to ${url} with auth token...`);
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ type: 'cek_lainnya' })
        });
        
        console.log('Status Code:', response.status);
        const text = await response.text();
        console.log('Response text:', text);
    } catch (e) {
        console.error('Fetch error:', e);
    }
}

test();

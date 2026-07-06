const crypto = require('crypto');

async function simulate() {
    const secret = "MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13";
    const header = { alg: 'HS256', typ: 'JWT' };
    const now = Math.floor(Date.now() / 1000);
    
    // User ID of Seiman Zega
    const payload = {
        id: "p5ntsk0nv4a0c2aqyxjdwl7y",
        role: "user",
        iat: now,
        exp: now + 24 * 3600
    };
    
    const base64url = (buf) => buf.toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    
    const headerStr = base64url(Buffer.from(JSON.stringify(header)));
    const payloadStr = base64url(Buffer.from(JSON.stringify(payload)));
    
    const dataToSign = `${headerStr}.${payloadStr}`;
    const signature = crypto.createHmac('sha256', secret).update(dataToSign).digest();
    const signatureStr = base64url(signature);
    
    const token = `${headerStr}.${payloadStr}.${signatureStr}`;
    console.log("Generated JWT Token for Seiman Zega:", token);
    
    // Call the watch-video API
    const url = 'https://api.shortlovers.id/api/rewards/watch-video';
    console.log(`\nCalling POST ${url}...`);
    
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ type: 'cek_lainnya' })
        });
        
        console.log("Response Status:", res.status);
        const text = await res.text();
        console.log("Response Body:", text);
    } catch (e) {
        console.error("Fetch failed:", e);
    }
}

simulate();

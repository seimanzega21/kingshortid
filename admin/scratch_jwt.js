const crypto = require('crypto');

function base64urlDecode(str) {
    let base64 = str.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4) {
        base64 += '=';
    }
    const binary = Buffer.from(base64, 'base64').toString('binary');
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}

async function verifyJwt(token, secret) {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        const [headerStr, payloadStr, signatureStr] = parts;
        
        const encoder = new TextEncoder();
        const dataToVerify = encoder.encode(`${headerStr}.${payloadStr}`);
        const signatureBytes = base64urlDecode(signatureStr);
        
        const secretBytes = encoder.encode(secret);
        const key = await crypto.webcrypto.subtle.importKey(
            'raw',
            secretBytes,
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['verify']
        );
        
        const isValid = await crypto.webcrypto.subtle.verify('HMAC', key, signatureBytes, dataToVerify);
        if (!isValid) return { error: 'invalid signature' };
        
        const decoder = new TextDecoder();
        const payloadBytes = base64urlDecode(payloadStr);
        const payloadJson = decoder.decode(payloadBytes);
        const payload = JSON.parse(payloadJson);
        
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp && now >= payload.exp) {
            return { error: 'expired', payload };
        }
        
        return { success: true, payload };
    } catch (e) {
        return { error: e.message };
    }
}

// Let's sign a token using jose-equivalent or similar Node crypto sign
async function test() {
    const secret = "MYt4Si3dPkRYUtR4EVyaXsnv/MCLmn3jJzJSKxTyClVdX2mxPmcfOY4/CPj1c3012c13";
    const header = { alg: 'HS256', typ: 'JWT' };
    const now = Math.floor(Date.now() / 1000);
    const payload = {
        id: "test-user-id",
        role: "admin",
        iat: now,
        exp: now + 7 * 24 * 3600
    };
    
    const base64url = (buf) => buf.toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    
    const headerStr = base64url(Buffer.from(JSON.stringify(header)));
    const payloadStr = base64url(Buffer.from(JSON.stringify(payload)));
    
    const dataToSign = `${headerStr}.${payloadStr}`;
    const signature = crypto.createHmac('sha256', secret).update(dataToSign).digest();
    const signatureStr = base64url(signature);
    
    const token = `${headerStr}.${payloadStr}.${signatureStr}`;
    console.log("Token:", token);
    
    const verificationResult = await verifyJwt(token, secret);
    console.log("Verification result:", verificationResult);
}

test();

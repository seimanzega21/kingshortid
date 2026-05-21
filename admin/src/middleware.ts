import { NextRequest, NextResponse } from 'next/server';

function base64urlEncode(arr: Uint8Array): string {
    let binary = '';
    const len = arr.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(arr[i]);
    }
    const base64 = btoa(binary);
    return base64
        .replace(/=/g, '')
        .replace(/\+/g, '-')
        .replace(/\//g, '_');
}

function base64urlDecode(str: string): Uint8Array {
    let base64 = str.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4) {
        base64 += '=';
    }
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
}

async function verifyJwt(token: string, secret: string) {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        const [headerStr, payloadStr, signatureStr] = parts;
        
        const encoder = new TextEncoder();
        const dataToVerify = encoder.encode(`${headerStr}.${payloadStr}`);
        const signatureBytes = base64urlDecode(signatureStr);
        
        const secretBytes = encoder.encode(secret);
        const key = await crypto.subtle.importKey(
            'raw',
            secretBytes,
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['verify']
        );
        
        const isValid = await crypto.subtle.verify('HMAC', key, signatureBytes, dataToVerify);
        if (!isValid) return null;
        
        const decoder = new TextDecoder();
        const payloadBytes = base64urlDecode(payloadStr);
        const payloadJson = decoder.decode(payloadBytes);
        const payload = JSON.parse(payloadJson);
        
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp && now >= payload.exp) {
            return null;
        }
        
        return payload;
    } catch (e) {
        console.error('JWT verification error in middleware:', e);
        return null;
    }
}

async function signJwt(payload: any, secret: string, expiresInSeconds: number = 7 * 24 * 3600) {
    const header = { alg: 'HS256', typ: 'JWT' };
    const encoder = new TextEncoder();
    
    const now = Math.floor(Date.now() / 1000);
    const fullPayload = {
        ...payload,
        iat: now,
        exp: now + expiresInSeconds
    };
    
    const headerBase64 = base64urlEncode(encoder.encode(JSON.stringify(header)));
    const payloadBase64 = base64urlEncode(encoder.encode(JSON.stringify(fullPayload)));
    const dataToSign = encoder.encode(`${headerBase64}.${payloadBase64}`);
    
    const secretBytes = encoder.encode(secret);
    const key = await crypto.subtle.importKey(
        'raw',
        secretBytes,
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
    );
    
    const signatureBuffer = await crypto.subtle.sign('HMAC', key, dataToSign);
    const signatureBase64 = base64urlEncode(new Uint8Array(signatureBuffer));
    
    return `${headerBase64}.${payloadBase64}.${signatureBase64}`;
}

const BYPASS_PATHS = [
    '/api/admin/auth/login',
    '/api/admin/auth/register',
    '/api/health'
];

export async function middleware(request: NextRequest) {
    const pathname = request.nextUrl.pathname;
    
    if (BYPASS_PATHS.some(path => pathname === path)) {
        return NextResponse.next();
    }

    const adminToken = request.cookies.get('admin_token')?.value;

    if (!adminToken) {
        return NextResponse.json(
            { message: 'Unauthorized. Admin session cookie missing.' },
            { status: 401 }
        );
    }

    const secret = process.env.JWT_SECRET;
    if (!secret) {
        return NextResponse.json(
            { message: 'Server configuration error. JWT_SECRET is missing.' },
            { status: 500 }
        );
    }

    const payload = await verifyJwt(adminToken, secret);
    if (!payload) {
        return NextResponse.json(
            { message: 'Unauthorized. Invalid or expired admin token.' },
            { status: 401 }
        );
    }

    if (payload.role !== 'admin') {
        return NextResponse.json(
            { message: 'Forbidden. Administrator privileges required.' },
            { status: 403 }
        );
    }

    const requestHeaders = new Headers(request.headers);
    const adminKey = process.env.ADMIN_API_KEY;
    if (adminKey) {
        requestHeaders.set('X-Admin-Key', adminKey);
    }

    const now = Math.floor(Date.now() / 1000);
    const iat = payload.iat || 0;
    const exp = payload.exp || 0;
    const age = now - iat;
    const timeLeft = exp - now;

    const shouldRenew = age > 3600 || timeLeft < 3 * 24 * 3600;

    let response = NextResponse.next({
        request: { headers: requestHeaders },
    });

    if (shouldRenew) {
        try {
            const renewedToken = await signJwt(
                { id: payload.id, role: payload.role },
                secret,
                7 * 24 * 3600
            );

            response.cookies.set('admin_token', renewedToken, {
                httpOnly: true,
                secure: process.env.NODE_ENV === 'production',
                sameSite: 'strict',
                maxAge: 7 * 24 * 60 * 60,
                path: '/',
            });
        } catch (e) {
            console.error('Failed to renew admin token:', e);
        }
    }

    return response;
}

export const config = {
    matcher: '/api/:path*',
};

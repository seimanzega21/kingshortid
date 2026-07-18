import { NextRequest, NextResponse } from 'next/server';

// Gunakan BACKEND_URL (http://kingshortid-api:3000/api) agar tidak error infinite loop ke localhost
const BACKEND_API = process.env.BACKEND_URL || 'http://kingshortid-api:3000/api';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        // Mengirim langsung ke Endpoint Server Produksi dari Backend (VPS / Cloudflare)
        const res = await fetch(`${BACKEND_API}/notifications/broadcast`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': ADMIN_KEY,
            },
            body: JSON.stringify(body),
        });

        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Broadcast proxy error:', error);
        return NextResponse.json({ error: 'Failed to send broadcast' }, { status: 500 });
    }
}

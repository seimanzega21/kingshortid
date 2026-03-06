import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.shortlovers.id';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        const res = await fetch(`${API_URL}/api/notifications/broadcast`, {
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

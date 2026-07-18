import { NextRequest, NextResponse } from 'next/server';

// In-memory cache — short TTL to keep user count in sync with /users page
let cache: { data: any; ts: number } | null = null;
const CACHE_TTL = 10_000; // 10 seconds — keeps totalUsers in sync

const BACKEND = process.env.BACKEND_URL || 'http://kingshortid-api:3000/api';
const VPS_API = `${BACKEND}/admin/dashboard`;

// GET /api/dashboard — Stats from VPS Backend API
export async function GET(request: NextRequest) {
    const adminKey = process.env.ADMIN_API_KEY || '';
    try {
        // Return cached data if fresh (instant response)
        if (cache && Date.now() - cache.ts < CACHE_TTL) {
            return NextResponse.json(cache.data);
        }

        const res = await fetch(VPS_API, {
            headers: { 'X-Admin-Key': adminKey },
            cache: 'no-store', // always fresh from VPS
        });

        if (!res.ok) {
            throw new Error(`VPS API error: ${res.status}`);
        }

        const data = await res.json();

        // Cache for 30 seconds
        cache = { data, ts: Date.now() };

        return NextResponse.json(data);
    } catch (error) {
        console.error('Dashboard error:', error);
        return NextResponse.json(
            { message: 'Failed to fetch dashboard stats' },
            { status: 500 }
        );
    }
}

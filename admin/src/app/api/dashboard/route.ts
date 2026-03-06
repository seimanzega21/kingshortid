import { NextRequest, NextResponse } from 'next/server';

// In-memory cache — dashboard doesn't need real-time data
let cache: { data: any; ts: number } | null = null;
const CACHE_TTL = 30_000; // 30 seconds

const VPS_API = 'https://api.shortlovers.id/api/admin/dashboard';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

// GET /api/dashboard — Stats from VPS Backend API
export async function GET(request: NextRequest) {
    try {
        // Return cached data if fresh (instant response)
        if (cache && Date.now() - cache.ts < CACHE_TTL) {
            return NextResponse.json(cache.data);
        }

        const res = await fetch(VPS_API, {
            headers: { 'X-Admin-Key': ADMIN_KEY },
            next: { revalidate: 30 },
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

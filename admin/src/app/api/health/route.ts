import { NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL || 'http://kingshortid-api:3000/api';
const VPS_API = `${BACKEND}/admin/dashboard`;

export const dynamic = 'force-dynamic';
export const revalidate = 0;

// GET /api/health — Check VPS backend connection status
export async function GET() {
    const adminKey = process.env.ADMIN_API_KEY || '';

    const result: {
        status: string;
        database: { connected: boolean; type: string; latency?: number; error?: string };
        timestamp: string;
    } = {
        status: 'ok',
        database: { connected: false, type: 'postgresql (supabase)' },
        timestamp: new Date().toISOString(),
    };

    try {
        const start = Date.now();
        const res = await fetch(VPS_API, {
            headers: { 'X-Admin-Key': adminKey },
            cache: 'no-store',
        });
        const latency = Date.now() - start;

        if (res.ok) {
            result.database.connected = true;
            result.database.latency = latency;
        } else {
            result.status = 'degraded';
            result.database.error = `API returned ${res.status}`;
        }
    } catch (error: any) {
        result.status = 'degraded';
        result.database.connected = false;
        result.database.error = error.message;
    }

    return NextResponse.json(result, {
        status: 200, // Always 200 to allow UI to show error details
    });
}

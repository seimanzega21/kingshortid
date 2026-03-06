import { NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/health — Check database connection status
export async function GET() {
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
        await prisma.$queryRawUnsafe('SELECT 1');
        const latency = Date.now() - start;

        result.database.connected = true;
        result.database.latency = latency;
    } catch (error: any) {
        result.status = 'degraded';
        result.database.connected = false;
        result.database.error = error.message;
    }

    return NextResponse.json(result, {
        status: result.status === 'ok' ? 200 : 503,
    });
}

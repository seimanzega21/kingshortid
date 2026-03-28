import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL || 'https://api.shortlovers.id/api';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

// GET /api/users — proxy to production backend
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const res = await fetch(`${BACKEND}/admin/users?${searchParams.toString()}`, {
            headers: { 'X-Admin-Key': ADMIN_KEY },
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Get users error:', error);
        return NextResponse.json({ message: 'Failed to fetch users' }, { status: 500 });
    }
}

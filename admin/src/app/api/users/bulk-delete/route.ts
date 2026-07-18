import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL || 'http://kingshortid-api:3000/api';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

// POST /api/users/bulk-delete
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const res = await fetch(`${BACKEND}/admin/users/bulk-delete`, {
            method: 'POST',
            headers: { 'X-Admin-Key': ADMIN_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Bulk delete error:', error);
        return NextResponse.json({ message: 'Failed to delete users' }, { status: 500 });
    }
}

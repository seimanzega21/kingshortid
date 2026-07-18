import { NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL || 'http://kingshortid-api:3000/api';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

export async function GET() {
    try {
        const res = await fetch(`${BACKEND}/admin/users/online`, {
            headers: { 'X-Admin-Key': ADMIN_KEY },
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Online users error:', error);
        return NextResponse.json({ message: 'Failed to fetch online users' }, { status: 500 });
    }
}
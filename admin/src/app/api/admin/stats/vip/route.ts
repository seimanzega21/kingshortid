import { NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL || 'http://kingshortid-api:3000/api';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

export async function GET() {
    try {
        const res = await fetch(`${BACKEND}/admin/stats/vip`, {
            headers: { 'X-Admin-Key': ADMIN_KEY },
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('VIP stats error:', error);
        return NextResponse.json({ message: 'Failed to fetch VIP stats' }, { status: 500 });
    }
}
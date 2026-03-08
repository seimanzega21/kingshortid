import { NextRequest, NextResponse } from 'next/server';

const VPS_API = 'https://api.shortlovers.id/api/auth/login';

// POST /api/admin/auth/login — Authenticate via VPS backend
export async function POST(request: NextRequest) {
    try {
        const { email, password } = await request.json();

        if (!email || !password) {
            return NextResponse.json(
                { message: 'Email and password are required' },
                { status: 400 }
            );
        }

        // Authenticate via VPS backend
        const res = await fetch(VPS_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
            cache: 'no-store',
        });

        const data = await res.json();

        if (!res.ok) {
            return NextResponse.json(
                { message: data.message || 'Invalid credentials' },
                { status: res.status }
            );
        }

        // Verify admin role
        if (data.user?.role !== 'admin') {
            return NextResponse.json(
                { message: 'Access denied. Administrator privileges required.' },
                { status: 403 }
            );
        }

        return NextResponse.json({ token: data.token, user: data.user }, { status: 200 });
    } catch (error) {
        console.error('Admin Login error:', error);
        return NextResponse.json(
            { message: 'Login failed' },
            { status: 500 }
        );
    }
}

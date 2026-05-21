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

        const response = NextResponse.json({ token: data.token, user: data.user }, { status: 200 });
        
        // Set the admin_token cookie securely
        response.cookies.set('admin_token', data.token, {
            httpOnly: true,
            secure: false,
            sameSite: 'strict',
            maxAge: 7 * 24 * 60 * 60, // 7 days
            path: '/',
        });

        return response;
    } catch (error) {
        console.error('Admin Login error:', error);
        return NextResponse.json(
            { message: 'Login failed' },
            { status: 500 }
        );
    }
}

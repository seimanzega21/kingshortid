import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
    const response = NextResponse.json({ success: true, message: 'Logged out successfully' }, { status: 200 });

    // Clear the admin_token cookie
    response.cookies.set('admin_token', '', {
        httpOnly: true,
        secure: false,
        sameSite: 'strict',
        maxAge: 0,
        path: '/',
    });

    return response;
}

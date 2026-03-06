import { NextRequest, NextResponse } from 'next/server';

// Add X-Admin-Key header to all proxied API requests going to VPS
export function middleware(request: NextRequest) {
    const adminKey = process.env.ADMIN_API_KEY;

    // Only modify requests that will be proxied to VPS via rewrites
    if (adminKey && request.nextUrl.pathname.startsWith('/api/')) {
        const requestHeaders = new Headers(request.headers);
        requestHeaders.set('X-Admin-Key', adminKey);

        return NextResponse.next({
            request: { headers: requestHeaders },
        });
    }

    return NextResponse.next();
}

export const config = {
    matcher: '/api/:path*',
};

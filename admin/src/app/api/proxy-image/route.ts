import { NextRequest, NextResponse } from 'next/server';

// GET /api/proxy-image?url=<encoded_url>
// Proxies R2 images to bypass browser content-type issues
export async function GET(request: NextRequest) {
    const url = request.nextUrl.searchParams.get('url');

    if (!url) {
        return NextResponse.json({ error: 'URL parameter required' }, { status: 400 });
    }

    // Only allow proxying from our own R2 domains
    const allowedHosts = [
        'https://stream.shortlovers.id/',
        'https://pub-8becf1ee9a914fc3a6525e2b50f11d04.r2.dev/',
    ];
    if (!allowedHosts.some(h => url.startsWith(h))) {
        return NextResponse.json({ error: 'Domain not allowed' }, { status: 403 });
    }

    try {
        const fetchUrl = url.includes('?') ? `${url}&v=2` : `${url}?v=2`;
        const response = await fetch(fetchUrl, {
            headers: { 'User-Agent': 'KingShort-Admin/1.0' },
            signal: AbortSignal.timeout(15000),
        });

        if (!response.ok) {
            return NextResponse.json({ error: `Upstream ${response.status}` }, { status: response.status });
        }

        const buffer = await response.arrayBuffer();

        // Force correct Content-Type from extension
        const ext = url.split('?')[0].split('.').pop()?.toLowerCase() || '';
        const ctMap: Record<string, string> = {
            webp: 'image/webp', jpg: 'image/jpeg', jpeg: 'image/jpeg',
            png: 'image/png', gif: 'image/gif',
        };

        return new NextResponse(buffer, {
            status: 200,
            headers: {
                'Content-Type': ctMap[ext] || 'image/webp',
                'Cache-Control': 'public, max-age=604800, s-maxage=2592000',
                'Access-Control-Allow-Origin': '*',
            },
        });
    } catch (error: any) {
        console.error('Proxy image error:', error.message);
        return NextResponse.json(
            { error: error.message || 'Failed to proxy image' },
            { status: 500 }
        );
    }
}




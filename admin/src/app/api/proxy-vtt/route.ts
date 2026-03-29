import { NextResponse } from 'next/server';

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const targetUrl = searchParams.get('url');

        if (!targetUrl) {
            return new Response('Missing url parameter', { status: 400 });
        }

        const res = await fetch(targetUrl);
        
        if (!res.ok) {
            return new Response(`Failed to fetch from CDN: ${res.status}`, { status: res.status });
        }

        const text = await res.text();

        return new Response(text, {
            headers: {
                'Content-Type': 'text/vtt; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=3600'
            }
        });
    } catch (e: any) {
        console.error("VTT Proxy Error:", e);
        return new Response(e.message || "Failed to proxy VTT", { status: 500 });
    }
}

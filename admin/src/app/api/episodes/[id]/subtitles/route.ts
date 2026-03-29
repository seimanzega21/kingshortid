import { NextResponse } from 'next/server';

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
    try {
        const { id } = await params;
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || 'https://api.shortlovers.id/api';
        const url = `${backendUrl}/episodes/${id}/subtitles`;
        
        const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
        
        if (!res.ok) {
            return NextResponse.json({ error: `Backend API returned status ${res.status}` }, { status: res.status });
        }
        
        const data = await res.json();
        return NextResponse.json(data);
    } catch (e: any) {
        console.error("Proxy subtitle fetch error:", e);
        return NextResponse.json({ error: e.message || "Failed to proxy subtitle request" }, { status: 500 });
    }
}

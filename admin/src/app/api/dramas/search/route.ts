import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

function escapeRegExp(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function computeRelevance(d: { title?: string | null; description?: string | null }, query: string, words: string[]): number {
    const title = (d.title || '').trim().toLowerCase();
    const desc = (d.description || '').trim().toLowerCase();
    const q = query.trim().toLowerCase();
    if (!q) return 0;

    // 1. Exact match 100% on title
    if (title === q) return 2000;

    // 2. Starts with query
    if (title.startsWith(q)) return 600;

    let score = 0;

    // 3. Contains full phrase in title
    if (title.includes(q)) {
        score += 350;
    }

    // 4. Token matches in title
    let titleWordsMatched = 0;
    for (const w of words) {
        if (title.includes(w)) {
            titleWordsMatched++;
            let isWordBoundary = false;
            try {
                isWordBoundary = new RegExp(`\\b${escapeRegExp(w)}\\b`, 'i').test(title);
            } catch {
                isWordBoundary = false;
            }
            score += isWordBoundary ? 80 : 40;
        }
    }

    // Huge bonus if ALL query words are in the title (order independent)
    if (words.length > 1 && titleWordsMatched === words.length) {
        score += 300;
    } else if (words.length > 1 && titleWordsMatched > 0) {
        score += Math.round((titleWordsMatched / words.length) * 100);
    }

    // 5. Matches in description
    if (desc.includes(q)) {
        score += 30;
    }
    for (const w of words) {
        if (w.length >= 3 && desc.includes(w)) {
            let isWordBoundary = false;
            try {
                isWordBoundary = new RegExp(`\\b${escapeRegExp(w)}\\b`, 'i').test(desc);
            } catch {
                isWordBoundary = false;
            }
            score += isWordBoundary ? 10 : 3;
        }
    }

    return score;
}

// GET /api/dramas/search
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const q = searchParams.get('q');
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '20');

        if (!q || !q.trim()) return NextResponse.json({ dramas: [], total: 0 });

        const cleanQuery = q.trim();
        const words = cleanQuery.toLowerCase().split(/\s+/).filter(w => w.length > 0);
        if (words.length === 0) return NextResponse.json({ dramas: [], total: 0 });

        const orConditions: any[] = [
            { title: { contains: cleanQuery, mode: 'insensitive' } },
            { description: { contains: cleanQuery, mode: 'insensitive' } },
        ];

        for (const w of words) {
            if (w.length >= 2) {
                orConditions.push({ title: { contains: w, mode: 'insensitive' } });
                orConditions.push({ description: { contains: w, mode: 'insensitive' } });
            } else {
                orConditions.push({ title: { contains: w, mode: 'insensitive' } });
            }
        }

        const candidateDramas = await prisma.drama.findMany({
            where: {
                isActive: true,
                OR: orConditions,
            },
            take: 500,
            orderBy: { views: 'desc' },
        });

        const scoredDramas = candidateDramas
            .map(d => ({
                drama: d,
                score: computeRelevance(d, cleanQuery, words),
            }))
            .filter(x => x.score > 0)
            .sort((a, b) => b.score - a.score || (b.drama.views || 0) - (a.drama.views || 0));

        const total = scoredDramas.length;
        const startIndex = (page - 1) * limit;
        const dramas = scoredDramas.slice(startIndex, startIndex + limit).map(x => x.drama);

        return NextResponse.json({ dramas, total, page });
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

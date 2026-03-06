import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/scraper/audit — Run data quality audit
export async function GET(request: NextRequest) {
    try {
        const dramas = await prisma.drama.findMany({
            where: { isActive: true },
            select: {
                id: true, title: true, cover: true, description: true,
                genres: true, totalEpisodes: true, status: true,
                _count: { select: { episodes: true } }
            },
            orderBy: { title: 'asc' },
        });

        const issues: Array<{
            id: string; title: string; problems: string[];
            cover: string; totalEpisodes: number;
        }> = [];

        let brokenCover = 0, badDesc = 0, genericGenre = 0, noEps = 0, mismatchEps = 0;

        for (const d of dramas) {
            const probs: string[] = [];

            // Cover check (URL pattern only — not HEAD check for speed)
            if (!d.cover || d.cover === '') {
                brokenCover++;
                probs.push('NO_COVER');
            }

            // Description
            if (!d.description || d.description === d.title || d.description.length < 10) {
                badDesc++;
                probs.push('BAD_DESC');
            }

            // Genre
            const g = d.genres as string[];
            if (!g || g.length === 0 || (g.length === 1 && g[0] === 'Drama')) {
                genericGenre++;
                probs.push('GENERIC_GENRE');
            }

            // Episodes
            if (d._count.episodes === 0) {
                noEps++;
                probs.push('NO_EPISODES');
            }

            // Episode count mismatch
            if (d.totalEpisodes !== d._count.episodes && d._count.episodes > 0) {
                mismatchEps++;
                probs.push(`EP_MISMATCH(db=${d.totalEpisodes},actual=${d._count.episodes})`);
            }

            if (probs.length > 0) {
                issues.push({
                    id: d.id,
                    title: d.title,
                    problems: probs,
                    cover: d.cover || '',
                    totalEpisodes: d._count.episodes,
                });
            }
        }

        // Deactivated dramas
        const deactivated = await prisma.drama.findMany({
            where: { isActive: false },
            select: { id: true, title: true, cover: true, totalEpisodes: true },
            orderBy: { title: 'asc' },
        });

        return NextResponse.json({
            total: dramas.length,
            healthy: dramas.length - issues.length,
            summary: {
                brokenCover,
                badDescription: badDesc,
                genericGenre,
                noEpisodes: noEps,
                episodeMismatch: mismatchEps,
            },
            issues,
            deactivated: deactivated.map(d => ({
                id: d.id,
                title: d.title,
                cover: d.cover || '',
                totalEpisodes: d.totalEpisodes,
            })),
        });
    } catch (error) {
        console.error('Scraper Audit Error:', error);
        return NextResponse.json({ message: 'Audit failed' }, { status: 500 });
    }
}

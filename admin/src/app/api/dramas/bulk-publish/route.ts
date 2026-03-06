import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// POST /api/dramas/bulk-publish — Activate all dramas that are ready
export async function POST(request: NextRequest) {
    try {
        // Find all inactive dramas that have cover, description, and episodes
        const inactiveDramas = await prisma.drama.findMany({
            where: { isActive: false },
            select: {
                id: true,
                title: true,
                cover: true,
                description: true,
                totalEpisodes: true,
                genres: true,
            },
        });

        const ready: string[] = [];
        const notReady: Array<{ title: string; issues: string[] }> = [];

        for (const d of inactiveDramas) {
            const issues: string[] = [];
            if (!d.cover || d.cover.length < 5) issues.push('NO_COVER');
            if (!d.description || d.description.length < 10 || d.description === d.title) issues.push('BAD_DESC');
            if (d.totalEpisodes === 0) issues.push('NO_EPISODES');

            if (issues.length === 0) {
                ready.push(d.id);
            } else {
                notReady.push({ title: d.title, issues });
            }
        }

        // Activate all ready dramas
        if (ready.length > 0) {
            await prisma.drama.updateMany({
                where: { id: { in: ready } },
                data: { isActive: true },
            });
        }

        return NextResponse.json({
            message: `${ready.length} dramas published, ${notReady.length} still have issues`,
            published: ready.length,
            remaining: notReady.length,
            notReady,
        });
    } catch (error) {
        console.error('Bulk publish error:', error);
        return NextResponse.json({ message: 'Failed to publish dramas' }, { status: 500 });
    }
}

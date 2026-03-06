import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/seasons - Get seasons for a drama
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const dramaId = searchParams.get('dramaId');

        if (!dramaId) {
            return NextResponse.json(
                { error: 'dramaId is required' },
                { status: 400 }
            );
        }

        const seasons = await prisma.season.findMany({
            where: { dramaId },
            orderBy: { seasonNumber: 'asc' },
            include: {
                _count: {
                    select: { episodes: true },
                },
            },
        });

        return NextResponse.json({ seasons });
    } catch (error: any) {
        console.error('Error fetching seasons:', error);
        return NextResponse.json(
            { error: 'Failed to fetch seasons' },
            { status: 500 }
        );
    }
}

// POST /api/seasons - Create a new season (admin only)
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user || user.role !== 'admin') {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { dramaId, seasonNumber, title, description, poster, releaseDate } = body;

        if (!dramaId || !seasonNumber || !title) {
            return NextResponse.json(
                { error: 'dramaId, seasonNumber, and title are required' },
                { status: 400 }
            );
        }

        const season = await prisma.season.create({
            data: {
                dramaId,
                seasonNumber,
                title,
                description,
                poster,
                releaseDate: releaseDate ? new Date(releaseDate) : undefined,
            },
        });

        return NextResponse.json(season, { status: 201 });
    } catch (error: any) {
        console.error('Error creating season:', error);
        return NextResponse.json(
            { error: 'Failed to create season' },
            { status: 500 }
        );
    }
}

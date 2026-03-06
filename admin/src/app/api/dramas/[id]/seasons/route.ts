import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

/**
 * GET /api/dramas/[id]/seasons
 * Get all seasons for a specific drama
 */
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        const seasons = await prisma.season.findMany({
            where: {
                dramaId: id,
            },
            orderBy: {
                seasonNumber: 'asc',
            },
            include: {
                _count: {
                    select: { episodes: true },
                },
            },
        });

        // Map to include actual episode count
        const seasonsWithCount = seasons.map((season) => ({
            ...season,
            episodeCount: season._count.episodes,
        }));

        return NextResponse.json(seasonsWithCount);
    } catch (error: any) {
        console.error('Error fetching seasons:', error);
        return NextResponse.json(
            { error: 'Failed to fetch seasons' },
            { status: 500 }
        );
    }
}

/**
 * POST /api/dramas/[id]/seasons
 * Create a new season for a drama (Admin only)
 */
export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id: dramaId } = await params;
        const body = await request.json();
        const { seasonNumber, title, description, poster, trailer, releaseDate } = body;

        // Validate required fields
        if (!seasonNumber || !title) {
            return NextResponse.json(
                { error: 'Season number and title are required' },
                { status: 400 }
            );
        }

        // Check if season number already exists for this drama
        const existing = await prisma.season.findUnique({
            where: {
                dramaId_seasonNumber: {
                    dramaId,
                    seasonNumber: parseInt(seasonNumber),
                },
            },
        });

        if (existing) {
            return NextResponse.json(
                { error: 'Season number already exists for this drama' },
                { status: 400 }
            );
        }

        // Create season
        const season = await prisma.season.create({
            data: {
                dramaId,
                seasonNumber: parseInt(seasonNumber),
                title,
                description,
                poster,
                trailer,
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

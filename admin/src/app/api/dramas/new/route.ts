import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/dramas/new - Get recently added dramas
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const limit = parseInt(searchParams.get('limit') || '10');

        const dramas = await prisma.drama.findMany({
            where: { isActive: true },
            orderBy: { createdAt: 'desc' },
            take: limit,
            select: {
                id: true,
                title: true,
                cover: true,
                rating: true,
                views: true,
                totalEpisodes: true,
                isVip: true,
                status: true,
                genres: true,
            }
        });
        return NextResponse.json(dramas);
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

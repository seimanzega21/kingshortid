import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

// GET /api/tags - Get all tags
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const type = searchParams.get('type'); // genre, mood, theme, style

        const where: any = {};
        if (type) where.type = type;

        const tags = await prisma.tag.findMany({
            where,
            orderBy: { name: 'asc' },
            include: {
                _count: {
                    select: { dramas: true },
                },
            },
        });

        return NextResponse.json({ tags });
    } catch (error: any) {
        console.error('Error fetching tags:', error);
        return NextResponse.json(
            { error: 'Failed to fetch tags' },
            { status: 500 }
        );
    }
}

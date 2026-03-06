import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/dramas/search
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const q = searchParams.get('q');
        const page = parseInt(searchParams.get('page') || '1');
        const limit = 20;

        if (!q) return NextResponse.json({ dramas: [], total: 0 });

        const [dramas, total] = await Promise.all([
            prisma.drama.findMany({
                where: {
                    isActive: true,
                    title: { contains: q, mode: 'insensitive' }
                },
                take: limit,
                skip: (page - 1) * limit,
                orderBy: { views: 'desc' }
            }),
            prisma.drama.count({
                where: {
                    isActive: true,
                    title: { contains: q, mode: 'insensitive' }
                }
            })
        ]);

        return NextResponse.json({ dramas, total });
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

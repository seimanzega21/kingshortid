import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/challenges - Get active challenges
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const type = searchParams.get('type'); // daily, weekly, special

        const now = new Date();
        const where: any = {
            isActive: true,
            startDate: { lte: now },
            endDate: { gte: now },
        };

        if (type) where.type = type;

        const challenges = await prisma.challenge.findMany({
            where,
            orderBy: { startDate: 'desc' },
        });

        return NextResponse.json({ challenges });
    } catch (error: any) {
        console.error('Error fetching challenges:', error);
        return NextResponse.json(
            { error: 'Failed to fetch challenges' },
            { status: 500 }
        );
    }
}

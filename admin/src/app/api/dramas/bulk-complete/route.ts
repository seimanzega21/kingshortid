import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// POST /api/dramas/bulk-complete — Mark all ongoing dramas as completed
export async function POST(request: NextRequest) {
    try {
        const result = await prisma.drama.updateMany({
            where: { status: 'ongoing' },
            data: { status: 'completed' },
        });

        return NextResponse.json({
            message: `${result.count} dramas marked as completed`,
            count: result.count,
        });
    } catch (error) {
        console.error('Bulk complete error:', error);
        return NextResponse.json({ message: 'Failed to complete dramas' }, { status: 500 });
    }
}

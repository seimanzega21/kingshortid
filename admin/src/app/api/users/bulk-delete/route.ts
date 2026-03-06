import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// POST /api/users/bulk-delete — Bulk delete users from Supabase
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { ids } = body;

        if (!ids || !Array.isArray(ids) || ids.length === 0) {
            return NextResponse.json(
                { message: 'No user IDs provided' },
                { status: 400 }
            );
        }

        const result = await prisma.user.deleteMany({
            where: { id: { in: ids } },
        });

        return NextResponse.json({
            message: `${result.count} users deleted`,
            count: result.count,
        });
    } catch (error) {
        console.error('Bulk delete error:', error);
        return NextResponse.json(
            { message: 'Failed to delete users' },
            { status: 500 }
        );
    }
}

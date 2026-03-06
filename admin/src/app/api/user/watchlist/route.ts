import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/user/watchlist
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const watchlist = await prisma.watchlist.findMany({
            where: { userId: user.id },
            include: { drama: true },
            orderBy: { addedAt: 'desc' }
        });

        return NextResponse.json(watchlist);
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

// POST /api/user/watchlist (Add)
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
        const { dramaId } = await request.json();

        await prisma.watchlist.create({
            data: { userId: user.id, dramaId }
        });

        return NextResponse.json({ success: true });
    } catch (error) {
        // Prisma unique constraint error likely if already exists
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

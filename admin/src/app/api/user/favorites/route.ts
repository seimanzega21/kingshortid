import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/user/favorites
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Auth required' }, { status: 401 });
        }

        const favorites = await prisma.favorite.findMany({
            where: { userId: user.id },
            include: { drama: true },
            orderBy: { addedAt: 'desc' },
        });

        return NextResponse.json(favorites);
    } catch (error) {
        return NextResponse.json({ message: 'Failed' }, { status: 500 });
    }
}

// POST /api/user/favorites
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Auth required' }, { status: 401 });
        }

        const { dramaId } = await request.json();

        await prisma.favorite.upsert({
            where: { userId_dramaId: { userId: user.id, dramaId } },
            create: { userId: user.id, dramaId },
            update: {},
        });

        // Increment drama likes
        await prisma.drama.update({
            where: { id: dramaId },
            data: { likes: { increment: 1 } },
        });

        return NextResponse.json({ message: 'Added to favorites' });
    } catch (error) {
        return NextResponse.json({ message: 'Failed' }, { status: 500 });
    }
}

// DELETE /api/user/favorites
export async function DELETE(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Auth required' }, { status: 401 });
        }

        const { dramaId } = await request.json();

        await prisma.favorite.deleteMany({
            where: { userId: user.id, dramaId },
        });

        // Decrement drama likes
        await prisma.drama.update({
            where: { id: dramaId },
            data: { likes: { decrement: 1 } },
        });

        return NextResponse.json({ message: 'Removed from favorites' });
    } catch (error) {
        return NextResponse.json({ message: 'Failed' }, { status: 500 });
    }
}

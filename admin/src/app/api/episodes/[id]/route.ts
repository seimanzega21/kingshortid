import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { requireAdmin } from '@/lib/auth';

// DELETE /api/episodes/[id]
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        await requireAdmin(request);
        const { id } = await params;

        // Decrement drama totalEpisodes (Transactional would be better but simple separate ops for now)
        const episode = await prisma.episode.findUnique({ where: { id } });
        if (episode) {
            await prisma.drama.update({
                where: { id: episode.dramaId },
                data: { totalEpisodes: { decrement: 1 } }
            });
            await prisma.episode.delete({ where: { id } });
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

// PATCH /api/episodes/[id]
export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        await requireAdmin(request);
        const { id } = await params;
        const body = await request.json();

        const updated = await prisma.episode.update({
            where: { id },
            data: {
                ...(body.isVip !== undefined && { isVip: body.isVip }),
                ...(body.coinPrice !== undefined && { coinPrice: parseInt(body.coinPrice) || 0 })
            }
        });

        return NextResponse.json(updated);
    } catch (error) {
        console.error("Error updating episode:", error);
        return NextResponse.json({ message: 'Error updating episode' }, { status: 500 });
    }
}

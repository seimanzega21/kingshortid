import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// DELETE /api/dramas/[id]/subtitles - Delete all subtitle relations for a drama
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        // Delete all subtitles where episode belongs to this drama
        const deleted = await prisma.subtitle.deleteMany({
            where: {
                episode: {
                    dramaId: id,
                },
            },
        });

        return NextResponse.json({
            success: true,
            count: deleted.count,
            message: `Berhasil menghapus ${deleted.count} relasi subtitle .vtt dari drama ini`,
        });
    } catch (error: any) {
        console.error('Delete drama subtitles error:', error);
        return NextResponse.json(
            { message: 'Gagal menghapus subtitle', error: error.message },
            { status: 500 }
        );
    }
}

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { requireAdmin } from '@/lib/auth';

/**
 * GET /api/tags/[id]
 * Get tag details with associated dramas
 */
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        const tag = await prisma.tag.findUnique({
            where: { id },
            include: {
                dramas: {
                    take: 10,
                    orderBy: { views: 'desc' },
                    select: {
                        id: true,
                        title: true,
                        cover: true,
                        rating: true,
                        views: true,
                        genres: true,
                    },
                },
                _count: {
                    select: { dramas: true },
                },
            },
        });

        if (!tag) {
            return NextResponse.json(
                { error: 'Tag not found' },
                { status: 404 }
            );
        }

        return NextResponse.json({
            ...tag,
            dramaCount: tag._count.dramas,
        });
    } catch (error: any) {
        console.error('Error fetching tag:', error);
        return NextResponse.json(
            { error: 'Failed to fetch tag' },
            { status: 500 }
        );
    }
}

/**
 * PUT /api/tags/[id]
 * Update tag (Admin only)
 */
export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        await requireAdmin(request);
        const { id } = await params;
        const body = await request.json();
        const { name, slug, type, color, icon } = body;

        const tag = await prisma.tag.update({
            where: { id },
            data: {
                name,
                slug,
                type,
                color,
                icon,
            },
        });

        return NextResponse.json(tag);
    } catch (error: any) {
        console.error('Error updating tag:', error);
        return NextResponse.json(
            { error: 'Failed to update tag' },
            { status: 500 }
        );
    }
}

/**
 * DELETE /api/tags/[id]
 * Delete tag (Admin only)
 */
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        await requireAdmin(request);
        const { id } = await params;

        await prisma.tag.delete({
            where: { id },
        });

        return NextResponse.json({ message: 'Tag deleted successfully' });
    } catch (error: any) {
        console.error('Error deleting tag:', error);
        return NextResponse.json(
            { error: 'Failed to delete tag' },
            { status: 500 }
        );
    }
}

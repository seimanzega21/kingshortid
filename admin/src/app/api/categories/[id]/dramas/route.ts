import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/categories/[id]/dramas
// [id] can be a cuid OR a slug here.
// But since the mobile app calls inputs slug (e.g. "romance"), 
// we assume 'id' receives the slug.
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const slug = id; // Treat the dynamic param 'id' as 'slug'

        // Find Category first (or just filter Dramas by genre string if simple)
        // Schema has `genres` as String[].
        // If Category model is just Metadata, and Drama stores "Action" in array...
        // Let's try to match the Drama.genres array containing Category.name

        const category = await prisma.category.findUnique({ where: { slug } });
        if (!category) return NextResponse.json({ message: 'Category not found' }, { status: 404 });

        const dramas = await prisma.drama.findMany({
            where: {
                isActive: true,
                genres: { has: category.name } // Filter where array contains name
            },
            orderBy: { views: 'desc' },
            take: 20
        });

        return NextResponse.json({ dramas, total: dramas.length });

    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

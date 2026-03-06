import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/dramas/banners - Get featured dramas for slider
export async function GET(request: NextRequest) {
    try {
        // Find dramas marked as featured, or just take top 5 random/popular if logic is simple
        const dramas = await prisma.drama.findMany({
            where: { isActive: true, isFeatured: true },
            orderBy: { updatedAt: 'desc' },
            take: 5,
            select: {
                id: true,
                title: true,
                description: true,
                cover: true, // Ideally we want a 'banner' field, schema has it? Yes: banner String?
                banner: true,
                isVip: true,
                genres: true
            }
        });

        // Fallback if no featured dramas
        if (dramas.length === 0) {
            const fallbacks = await prisma.drama.findMany({
                where: { isActive: true },
                orderBy: { views: 'desc' },
                take: 5,
                select: {
                    id: true,
                    title: true,
                    description: true,
                    cover: true,
                    banner: true,
                    isVip: true,
                    genres: true
                }
            });
            return NextResponse.json(fallbacks);
        }

        return NextResponse.json(dramas);
    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

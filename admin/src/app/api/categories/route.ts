import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { requireAdmin } from '@/lib/auth';

// GET /api/categories
export async function GET() {
    try {
        const categories = await prisma.category.findMany({
            orderBy: { order: 'asc' }
        });
        return NextResponse.json(categories);
    } catch (error) {
        return NextResponse.json({ message: 'Failed to fetch categories' }, { status: 500 });
    }
}

// POST /api/categories
export async function POST(request: NextRequest) {
    try {
        const data = await request.json();

        // Simple Slug Generation
        const slug = data.slug || data.name.toLowerCase().replace(/ /g, '-').replace(/[^\w-]+/g, '');

        const category = await prisma.category.create({
            data: {
                name: data.name,
                slug,
                icon: data.icon,
                order: data.order || 0
            }
        });
        return NextResponse.json(category, { status: 201 });
    } catch (error) {
        console.error("Create Category Error", error);
        return NextResponse.json({ message: 'Failed to create category' }, { status: 500 });
    }
}

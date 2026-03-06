import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// GET /api/reports - Get reported content
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const status = searchParams.get('status'); // pending, approved, rejected
        const type = searchParams.get('type'); // drama, comment, user

        const where: any = {};
        if (status && status !== 'all') where.status = status;
        if (type) where.type = type;

        const reports = await prisma.report.findMany({
            where,
            orderBy: { createdAt: 'desc' },
            include: {
                reporter: {
                    select: { id: true, name: true, email: true }
                }
            }
        });

        // Get counts
        const [pending, approved, rejected, total] = await Promise.all([
            prisma.report.count({ where: { status: 'pending' } }),
            prisma.report.count({ where: { status: 'approved' } }),
            prisma.report.count({ where: { status: 'rejected' } }),
            prisma.report.count()
        ]);

        return NextResponse.json({
            reports,
            counts: { pending, approved, rejected, total }
        });
    } catch (error) {
        console.error('Get reports error:', error);
        return NextResponse.json(
            { message: 'Failed to get reports' },
            { status: 500 }
        );
    }
}

// POST /api/reports - Create report
export async function POST(request: NextRequest) {
    try {
        const data = await request.json();

        const report = await prisma.report.create({
            data: {
                type: data.type, // drama, comment, user
                targetId: data.targetId,
                title: data.title,
                reason: data.reason,
                reporterId: data.reporterId,
                status: 'pending'
            }
        });

        return NextResponse.json(report, { status: 201 });
    } catch (error: any) {
        console.error('Create report error:', error);
        return NextResponse.json(
            { message: error.message || 'Failed to create report' },
            { status: 500 }
        );
    }
}

// PATCH /api/reports - Update report status
export async function PATCH(request: NextRequest) {
    try {
        const data = await request.json();
        const { id, status } = data;

        const report = await prisma.report.update({
            where: { id },
            data: { status }
        });

        return NextResponse.json(report);
    } catch (error: any) {
        console.error('Update report error:', error);
        return NextResponse.json(
            { message: error.message || 'Failed to update report' },
            { status: 500 }
        );
    }
}

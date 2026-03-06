import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { verifyToken } from '@/lib/auth';

// GET /api/coins/history - Get user's coin transaction history
export async function GET(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '');
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const decoded = verifyToken(token);
        if (!decoded) {
            return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
        }

        const { searchParams } = new URL(request.url);
        const page = parseInt(searchParams.get('page') || '1');
        const limit = parseInt(searchParams.get('limit') || '50');
        const skip = (page - 1) * limit;

        const [transactions, total] = await Promise.all([
            prisma.coinTransaction.findMany({
                where: { userId: decoded.id },
                orderBy: { createdAt: 'desc' },
                take: limit,
                skip,
                select: {
                    id: true,
                    type: true,
                    amount: true,
                    description: true,
                    balanceAfter: true,
                    createdAt: true,
                },
            }),
            prisma.coinTransaction.count({
                where: { userId: decoded.id },
            }),
        ]);

        return NextResponse.json({
            transactions,
            pagination: {
                page,
                limit,
                total,
                pages: Math.ceil(total / limit),
            },
        });
    } catch (error: any) {
        console.error('Coin history error:', error);
        return NextResponse.json(
            { error: 'Failed to fetch coin history', message: error.message },
            { status: 500 }
        );
    }
}

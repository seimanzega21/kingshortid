import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/coins/earn/ad
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const { adType } = await request.json(); // 'rewarded_video' typically

        // Limit Logic (e.g., max 5 ads per day) Could be added here.
        // For now, simpler logic. Give 5 coins.

        const reward = 5;

        const updatedUser = await prisma.user.update({
            where: { id: user.id },
            data: { coins: { increment: reward } }
        });

        await prisma.coinTransaction.create({
            data: {
                userId: user.id,
                type: 'earn',
                amount: reward,
                description: `Watch Ad (${adType || 'Reward'})`,
                balanceAfter: updatedUser.coins
            }
        });

        return NextResponse.json({
            success: true,
            coins: reward,
            newBalance: updatedUser.coins
        });

    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

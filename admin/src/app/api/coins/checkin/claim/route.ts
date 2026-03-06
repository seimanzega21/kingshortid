import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/coins/checkin/claim
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Auth required' }, { status: 401 });
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const lastCheckIn = user.lastCheckIn ? new Date(user.lastCheckIn) : null;
        const lastCheckInDay = lastCheckIn ? new Date(lastCheckIn.setHours(0, 0, 0, 0)) : null;

        // Check if already claimed today
        if (lastCheckInDay && lastCheckInDay.getTime() >= today.getTime()) {
            return NextResponse.json({ message: 'Already claimed today' }, { status: 400 });
        }

        // Calculate streak
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        let newStreak = 1;
        if (lastCheckInDay && lastCheckInDay.getTime() === yesterday.getTime()) {
            // Consecutive day
            newStreak = (user.checkInStreak % 7) + 1;
        }

        // Reward based on day
        const rewardMap: Record<number, number> = {
            1: 10, 2: 15, 3: 20, 4: 25, 5: 30, 6: 40, 7: 100,
        };
        const coins = rewardMap[newStreak] || 10;
        const newBalance = user.coins + coins;

        // Update user
        await prisma.user.update({
            where: { id: user.id },
            data: {
                coins: newBalance,
                lastCheckIn: new Date(),
                checkInStreak: newStreak,
            },
        });

        // Record transaction
        await prisma.coinTransaction.create({
            data: {
                userId: user.id,
                type: 'earn',
                amount: coins,
                description: `Daily check-in day ${newStreak}`,
                balanceAfter: newBalance,
            },
        });

        return NextResponse.json({
            coins,
            newBalance,
            streak: newStreak,
        });
    } catch (error) {
        return NextResponse.json({ message: 'Failed' }, { status: 500 });
    }
}

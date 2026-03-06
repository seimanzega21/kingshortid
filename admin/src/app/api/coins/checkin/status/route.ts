import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/coins/checkin/status
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Auth required' }, { status: 401 });
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const lastCheckIn = user.lastCheckIn ? new Date(user.lastCheckIn) : null;
        const lastCheckInDay = lastCheckIn ? new Date(lastCheckIn.setHours(0, 0, 0, 0)) : null;

        const canCheckIn = !lastCheckInDay || lastCheckInDay.getTime() < today.getTime();

        // Daily rewards schedule
        const rewards = [
            { day: 1, coins: 10, claimed: user.checkInStreak >= 1, claimable: canCheckIn && user.checkInStreak === 0 },
            { day: 2, coins: 15, claimed: user.checkInStreak >= 2, claimable: canCheckIn && user.checkInStreak === 1 },
            { day: 3, coins: 20, claimed: user.checkInStreak >= 3, claimable: canCheckIn && user.checkInStreak === 2 },
            { day: 4, coins: 25, claimed: user.checkInStreak >= 4, claimable: canCheckIn && user.checkInStreak === 3 },
            { day: 5, coins: 30, claimed: user.checkInStreak >= 5, claimable: canCheckIn && user.checkInStreak === 4 },
            { day: 6, coins: 40, claimed: user.checkInStreak >= 6, claimable: canCheckIn && user.checkInStreak === 5 },
            { day: 7, coins: 100, claimed: user.checkInStreak >= 7, claimable: canCheckIn && user.checkInStreak === 6 },
        ];

        return NextResponse.json({
            streak: user.checkInStreak,
            lastCheckIn: user.lastCheckIn,
            rewards,
            canCheckIn,
        });
    } catch (error) {
        return NextResponse.json({ message: 'Failed' }, { status: 500 });
    }
}

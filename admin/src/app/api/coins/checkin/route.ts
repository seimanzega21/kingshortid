import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/coins/checkin/status
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const dbUser = await prisma.user.findUnique({
            where: { id: user.id },
            select: { lastCheckIn: true, checkInStreak: true } // Assuming these fields exist in schema (Added them previously)
        });

        // Calculate Logic
        // If last checkin was yesterday, streak continues.
        // If today, already claimed.
        // If older, streak resets (logic can be complex, doing simple version)

        let streak = dbUser?.checkInStreak || 0;
        let canCheckIn = true;

        if (dbUser?.lastCheckIn) {
            const last = new Date(dbUser.lastCheckIn);
            const today = new Date();

            // Check if same day
            if (last.getDate() === today.getDate() &&
                last.getMonth() === today.getMonth() &&
                last.getFullYear() === today.getFullYear()) {
                canCheckIn = false;
            } else {
                // Check if broken streak (more than 1 day gap)
                const diffTime = Math.abs(today.getTime() - last.getTime());
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                if (diffDays > 2) { // Allow < 48 hours effectively
                    streak = 0; // Reset visual streak
                }
            }
        }

        const rewards = [
            { day: 1, coins: 5, claimed: streak >= 1, claimable: canCheckIn && streak === 0 },
            { day: 2, coins: 10, claimed: streak >= 2, claimable: canCheckIn && streak === 1 },
            { day: 3, coins: 15, claimed: streak >= 3, claimable: canCheckIn && streak === 2 },
            { day: 4, coins: 20, claimed: streak >= 4, claimable: canCheckIn && streak === 3 },
            { day: 5, coins: 25, claimed: streak >= 5, claimable: canCheckIn && streak === 4 },
            { day: 6, coins: 30, claimed: streak >= 6, claimable: canCheckIn && streak === 5 },
            { day: 7, coins: 50, claimed: streak >= 7, claimable: canCheckIn && streak === 6 },
        ];

        return NextResponse.json({
            streak,
            lastCheckIn: dbUser?.lastCheckIn,
            canCheckIn,
            rewards
        });

    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

// POST /api/coins/checkin/claim
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const result = await prisma.$transaction(async (tx) => {
            const dbUser = await tx.user.findUnique({ where: { id: user.id } });

            // Verify again (simple check)
            if (dbUser?.lastCheckIn) {
                const last = new Date(dbUser.lastCheckIn);
                const today = new Date();
                if (last.getDate() === today.getDate() && last.getMonth() === today.getMonth()) {
                    throw new Error("Already claimed");
                }
            }

            const newStreak = (dbUser?.checkInStreak || 0) + 1;

            // Reward logic
            let rewardCoins = 5;
            if (newStreak === 2) rewardCoins = 10;
            else if (newStreak === 3) rewardCoins = 15;
            else if (newStreak === 7) rewardCoins = 50;

            // Update User
            const updatedUser = await tx.user.update({
                where: { id: user.id },
                data: {
                    coins: { increment: rewardCoins },
                    lastCheckIn: new Date(),
                    checkInStreak: newStreak > 7 ? 1 : newStreak // Reset after 7? or keep going? Let's cap at 7 logic visually but typically it loops
                }
            });

            // Record Transaction
            await tx.coinTransaction.create({
                data: {
                    userId: user.id,
                    type: 'bonus',
                    amount: rewardCoins,
                    description: `Daily Check-In Day ${newStreak}`,
                    balanceAfter: updatedUser.coins
                }
            });

            return { coins: rewardCoins, newBalance: updatedUser.coins, streak: newStreak };
        });

        return NextResponse.json(result);

    } catch (error: any) {
        if (error.message === 'Already claimed') {
            return NextResponse.json({ message: 'Already claimed today' }, { status: 400 });
        }
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

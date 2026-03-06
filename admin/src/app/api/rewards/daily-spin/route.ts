import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { getAuthUser } from '@/lib/auth';

const prisma = new PrismaClient();

// Spin wheel reward tiers with probability weights
const SPIN_REWARDS = [
    { coins: 5, weight: 30, color: '#FF6B6B' },    // 30% - 5 coins
    { coins: 10, weight: 25, color: '#4ECDC4' },   // 25% - 10 coins
    { coins: 15, weight: 20, color: '#45B7D1' },   // 20% - 15 coins
    { coins: 25, weight: 15, color: '#FFD93D' },   // 15% - 25 coins
    { coins: 50, weight: 7, color: '#6BCB77' },    // 7% - 50 coins
    { coins: 100, weight: 2, color: '#C44569' },   // 2% - 100 coins
    { coins: 200, weight: 1, color: '#9B59B6' },   // 1% - 200 coins (JACKPOT!)
];

function getRandomReward() {
    const totalWeight = SPIN_REWARDS.reduce((sum, r) => sum + r.weight, 0);
    let random = Math.random() * totalWeight;

    for (const reward of SPIN_REWARDS) {
        random -= reward.weight;
        if (random <= 0) {
            return reward;
        }
    }

    return SPIN_REWARDS[0]; // fallback
}

// GET - Check if user can spin today
export async function GET(req: NextRequest) {
    try {
        const token = req.headers.get('authorization')?.replace('Bearer ', '');
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const payload = await getAuthUser(req);
        if (!payload || !payload.id) {
            return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
        }

        const user = await prisma.user.findUnique({
            where: { id: payload.id },
            select: {
                id: true,
                lastSpinDate: true,
                totalSpins: true,
                coins: true,
            },
        });

        if (!user) {
            return NextResponse.json({ error: 'User not found' }, { status: 404 });
        }

        // Check if user already spun today
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const lastSpinDate = user.lastSpinDate ? new Date(user.lastSpinDate) : null;
        const canSpin = !lastSpinDate || lastSpinDate < today;

        return NextResponse.json({
            canSpin,
            lastSpinDate: user.lastSpinDate,
            totalSpins: user.totalSpins,
            currentCoins: user.coins,
            rewardOptions: SPIN_REWARDS,
        });
    } catch (error) {
        console.error('Daily spin check error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

// POST - Spin the wheel and claim reward
export async function POST(req: NextRequest) {
    try {
        const token = req.headers.get('authorization')?.replace('Bearer ', '');
        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const payload = await getAuthUser(req);
        if (!payload || !payload.id) {
            return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
        }

        const user = await prisma.user.findUnique({
            where: { id: payload.id },
        });

        if (!user) {
            return NextResponse.json({ error: 'User not found' }, { status: 404 });
        }

        // Check if user already spun today
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const lastSpinDate = user.lastSpinDate ? new Date(user.lastSpinDate) : null;
        if (lastSpinDate && lastSpinDate >= today) {
            return NextResponse.json(
                { error: 'Anda sudah spin hari ini. Kembali lagi besok!' },
                { status: 400 }
            );
        }

        // Get random reward
        const reward = getRandomReward();

        // Update user coins and spin date
        const updatedUser = await prisma.user.update({
            where: { id: user.id },
            data: {
                coins: { increment: reward.coins },
                lastSpinDate: new Date(),
                totalSpins: { increment: 1 },
            },
        });

        // Record the reward
        await prisma.dailyReward.create({
            data: {
                userId: user.id,
                rewardType: 'spin_wheel',
                amount: reward.coins,
            },
        });

        // Record coin transaction
        await prisma.coinTransaction.create({
            data: {
                userId: user.id,
                type: 'earn',
                amount: reward.coins,
                description: `Hadiah Spin Harian: ${reward.coins} koin`,
                balanceAfter: updatedUser.coins,
            },
        });

        return NextResponse.json({
            success: true,
            reward: {
                coins: reward.coins,
                color: reward.color,
            },
            newBalance: updatedUser.coins,
            totalSpins: updatedUser.totalSpins,
            message: reward.coins >= 100
                ? '🎉 JACKPOT! Anda mendapat hadiah besar!'
                : `✨ Selamat! Anda mendapat ${reward.coins} koin!`,
        });
    } catch (error) {
        console.error('Daily spin error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

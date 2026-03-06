import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/coins/balance — returns split balance (purchased vs bonus)
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
        }

        const dbUser = await prisma.user.findUnique({
            where: { id: user.id },
            select: { coins: true },
        });

        // Calculate purchased coins (topup transactions)
        const purchased = await prisma.coinTransaction.aggregate({
            where: {
                userId: user.id,
                type: 'topup',
            },
            _sum: { amount: true },
        });

        // Calculate spent coins
        const spent = await prisma.coinTransaction.aggregate({
            where: {
                userId: user.id,
                type: 'spend',
            },
            _sum: { amount: true },
        });

        const totalCoins = dbUser?.coins || 0;
        const totalPurchased = purchased._sum.amount || 0;
        const totalSpent = Math.abs(spent._sum.amount || 0);

        // Purchased coins remaining = purchased - spent (but floor at 0)
        const purchasedRemaining = Math.max(0, totalPurchased - totalSpent);

        // Bonus coins = total - purchased remaining
        const bonusCoins = Math.max(0, totalCoins - purchasedRemaining);

        return NextResponse.json({
            totalCoins,
            purchasedCoins: purchasedRemaining,
            bonusCoins,
        });
    } catch (error) {
        console.error('Balance error:', error);
        return NextResponse.json({ message: 'Failed to get balance' }, { status: 500 });
    }
}

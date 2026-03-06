import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// POST /api/coins/spend - Unlock Episode
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });

        const { amount, episodeId } = await request.json();

        if (!episodeId || amount <= 0) {
            return NextResponse.json({ success: false, message: 'Invalid data' }, { status: 400 });
        }

        // Transaction Block for Safety
        const result = await prisma.$transaction(async (tx) => {
            // 1. Get User Balance with filtering (Double check)
            const dbUser = await tx.user.findUnique({ where: { id: user.id } });

            if (!dbUser || dbUser.coins < amount) {
                throw new Error("Insufficient balance");
            }

            // 2. Check if already unlocked (Optional, usually checked by client but good to have)
            // Assuming WatchHistory stores unlocked episodes or valid access.
            // For now, simpler logic: simple purchase record.

            // 3. Deduct Coins
            const updatedUser = await tx.user.update({
                where: { id: user.id },
                data: { coins: { decrement: amount } }
            });

            // 4. Record Transaction
            await tx.coinTransaction.create({
                data: {
                    userId: user.id,
                    type: 'spend',
                    amount: amount,
                    description: `Unlock Episode ${episodeId}`,
                    reference: episodeId,
                    balanceAfter: updatedUser.coins
                }
            });

            return updatedUser;
        });

        return NextResponse.json({
            success: true,
            newBalance: result.coins
        });

    } catch (error: any) {
        // console.error(error);
        if (error.message === 'Insufficient balance') {
            return NextResponse.json({ success: false, message: 'Saldo tidak cukup' }, { status: 402 });
        }
        return NextResponse.json({ success: false, message: 'Transaction Failed' }, { status: 500 });
    }
}

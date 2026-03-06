import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

/**
 * POST /api/challenges/[id]/claim
 * Claim challenge reward
 */
export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { id: challengeId } = await params;

        // Check if challenge exists and is active
        const challenge = await prisma.challenge.findUnique({
            where: { id: challengeId },
        });

        if (!challenge) {
            return NextResponse.json({ error: 'Challenge not found' }, { status: 404 });
        }

        if (!challenge.isActive) {
            return NextResponse.json({ error: 'Challenge is not active' }, { status: 400 });
        }

        const now = new Date();
        if (now < challenge.startDate || now > challenge.endDate) {
            return NextResponse.json({ error: 'Challenge is not available' }, { status: 400 });
        }

        // Check if user has completed the challenge
        const completion = await prisma.challengeCompletion.findUnique({
            where: {
                userId_challengeId: {
                    userId: user.id,
                    challengeId,
                },
            },
        });

        if (!completion || !completion.isCompleted) {
            return NextResponse.json(
                { error: 'Challenge not completed yet' },
                { status: 400 }
            );
        }

        if (completion.completedAt) {
            return NextResponse.json(
                { error: 'Reward already claimed' },
                { status: 400 }
            );
        }

        // Award coins
        await prisma.$transaction([
            // Update user coins
            prisma.user.update({
                where: { id: user.id },
                data: {
                    coins: {
                        increment: challenge.reward,
                    },
                },
            }),
            // Record transaction
            prisma.coinTransaction.create({
                data: {
                    userId: user.id,
                    type: 'earn',
                    amount: challenge.reward,
                    description: `Challenge completed: ${challenge.title}`,
                    reference: challengeId,
                },
            }),
            // Mark as claimed
            prisma.challengeCompletion.update({
                where: {
                    userId_challengeId: {
                        userId: user.id,
                        challengeId,
                    },
                },
                data: {
                    completedAt: now,
                },
            }),
        ]);

        return NextResponse.json({
            message: 'Reward claimed successfully',
            coins: challenge.reward,
        });
    } catch (error: any) {
        console.error('Error claiming challenge reward:', error);
        return NextResponse.json(
            { error: 'Failed to claim reward' },
            { status: 500 }
        );
    }
}

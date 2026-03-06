import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

/**
 * GET /api/challenges/progress
 * Get user's progress for all active challenges
 */
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const now = new Date();

        // Get all active challenges with user progress
        const challenges = await prisma.challenge.findMany({
            where: {
                isActive: true,
                startDate: { lte: now },
                endDate: { gte: now },
            },
            include: {
                completions: {
                    where: { userId: user.id },
                },
            },
            orderBy: { startDate: 'desc' },
        });

        const progress = challenges.map((challenge) => {
            const completion = challenge.completions[0];

            return {
                challenge: {
                    id: challenge.id,
                    title: challenge.title,
                    description: challenge.description,
                    icon: challenge.icon,
                    type: challenge.type,
                    requirement: challenge.requirement,
                    reward: challenge.reward,
                    startDate: challenge.startDate,
                    endDate: challenge.endDate,
                },
                progress: completion?.progress || 0,
                isCompleted: completion?.isCompleted || false,
                isClaimed: !!completion?.completedAt,
                completedAt: completion?.completedAt,
            };
        });

        return NextResponse.json({ progress });
    } catch (error: any) {
        console.error('Error fetching challenge progress:', error);
        return NextResponse.json(
            { error: 'Failed to fetch challenge progress' },
            { status: 500 }
        );
    }
}

/**
 * POST /api/challenges/progress/update
 * Update user progress for challenges
 */
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { challengeId, progress } = body;

        if (!challengeId || progress === undefined) {
            return NextResponse.json(
                { error: 'Challenge ID and progress are required' },
                { status: 400 }
            );
        }

        // Get challenge details
        const challenge = await prisma.challenge.findUnique({
            where: { id: challengeId },
        });

        if (!challenge) {
            return NextResponse.json({ error: 'Challenge not found' }, { status: 404 });
        }

        // Parse requirement (JSON string)
        const requirement = JSON.parse(challenge.requirement);
        const isCompleted = progress >= (requirement.target || challenge.requirement);

        // Upsert challenge completion
        const completion = await prisma.challengeCompletion.upsert({
            where: {
                userId_challengeId: {
                    userId: user.id,
                    challengeId,
                },
            },
            update: {
                progress,
                isCompleted,
            },
            create: {
                userId: user.id,
                challengeId,
                progress,
                isCompleted,
            },
        });

        return NextResponse.json({
            completion,
            challenge: {
                id: challenge.id,
                title: challenge.title,
                reward: challenge.reward,
            },
        });
    } catch (error: any) {
        console.error('Error updating challenge progress:', error);
        return NextResponse.json(
            { error: 'Failed to update progress' },
            { status: 500 }
        );
    }
}

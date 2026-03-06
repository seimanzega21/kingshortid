import { NextRequest, NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { getAuthUser } from '@/lib/auth';

const prisma = new PrismaClient();

// GET - Get user's achievements
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

        // Get all achievements with user unlock status
        const allAchievements = await prisma.achievement.findMany({
            where: { isActive: true },
            include: {
                users: {
                    where: { userId: payload.id },
                },
            },
            orderBy: { createdAt: 'asc' },
        });

        const achievements = allAchievements.map((achievement) => ({
            id: achievement.id,
            name: achievement.name,
            description: achievement.description,
            icon: achievement.icon,
            type: achievement.type,
            requirement: achievement.requirement,
            reward: achievement.reward,
            unlocked: achievement.users.length > 0,
            unlockedAt: achievement.users[0]?.unlockedAt || null,
        }));

        const unlockedCount = achievements.filter(a => a.unlocked).length;
        const totalCount = achievements.length;

        return NextResponse.json({
            achievements,
            stats: {
                unlocked: unlockedCount,
                total: totalCount,
                percentage: Math.round((unlockedCount / totalCount) * 100),
            },
        });
    } catch (error) {
        console.error('Get achievements error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}

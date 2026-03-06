import { NextRequest, NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/auth';
import { checkAchievements } from '@/lib/achievements';

// POST /api/achievements/check - Check and unlock achievements for user
export async function POST(request: NextRequest) {
    try {
        const authHeader = request.headers.get('authorization');
        if (!authHeader?.startsWith('Bearer ')) {
            return NextResponse.json({ error: 'No token provided' }, { status: 401 });
        }

        const user = await getAuthUser(request);
        if (!user || !user.id) {
            return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
        }

        const unlockedAchievements = await checkAchievements(user.id);

        return NextResponse.json({
            success: true,
            unlocked: unlockedAchievements,
        });
    } catch (error) {
        console.error('Achievement check error:', error);
        return NextResponse.json({ error: 'Failed to check achievements' }, { status: 500 });
    }
}

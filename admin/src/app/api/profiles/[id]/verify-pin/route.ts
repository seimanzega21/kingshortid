import { NextRequest, NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import bcrypt from 'bcryptjs';

/**
 * POST /api/profiles/[id]/verify-pin
 * Verify profile PIN for access
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

        const { id } = await params;
        const body = await request.json();
        const { pin } = body;

        if (!pin) {
            return NextResponse.json(
                { error: 'PIN is required' },
                { status: 400 }
            );
        }

        const profile = await prisma.profile.findUnique({
            where: { id },
        });

        if (!profile) {
            return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
        }

        if (profile.userId !== user.id) {
            return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
        }

        if (!profile.pin) {
            return NextResponse.json(
                { error: 'This profile has no PIN set' },
                { status: 400 }
            );
        }

        const isValid = await bcrypt.compare(pin, profile.pin);

        if (!isValid) {
            return NextResponse.json(
                { error: 'Incorrect PIN' },
                { status: 401 }
            );
        }

        return NextResponse.json({
            message: 'PIN verified successfully',
            profile: {
                id: profile.id,
                name: profile.name,
                avatar: profile.avatar,
            },
        });
    } catch (error: any) {
        console.error('Error verifying PIN:', error);
        return NextResponse.json(
            { error: 'Failed to verify PIN' },
            { status: 500 }
        );
    }
}

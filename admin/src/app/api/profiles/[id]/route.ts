import { NextRequest, NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import bcrypt from 'bcryptjs';

/**
 * GET /api/profiles/[id]
 * Get profile details
 */
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { id } = await params;

        const profile = await prisma.profile.findUnique({
            where: { id },
            include: {
                _count: {
                    select: { watchHistory: true },
                },
            },
        });

        if (!profile) {
            return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
        }

        // Verify ownership
        if (profile.userId !== user.id) {
            return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
        }

        return NextResponse.json({
            profile: {
                ...profile,
                hasPin: !!profile.pin,
                pin: undefined,
                watchHistoryCount: profile._count.watchHistory,
            },
        });
    } catch (error: any) {
        console.error('Error fetching profile:', error);
        return NextResponse.json(
            { error: 'Failed to fetch profile' },
            { status: 500 }
        );
    }
}

/**
 * PUT /api/profiles/[id]
 * Update profile
 */
export async function PUT(
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
        const { name, avatar, ageRating, pin, language, theme, autoPlay } = body;

        // Verify ownership
        const existingProfile = await prisma.profile.findUnique({
            where: { id },
        });

        if (!existingProfile) {
            return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
        }

        if (existingProfile.userId !== user.id) {
            return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
        }

        // Hash new PIN if provided
        const hashedPin = pin ? await bcrypt.hash(pin, 10) : undefined;

        const profile = await prisma.profile.update({
            where: { id },
            data: {
                name,
                avatar,
                ageRating,
                pin: hashedPin,
                language,
                theme,
                autoPlay,
            },
        });

        return NextResponse.json({
            profile: {
                ...profile,
                hasPin: !!profile.pin,
                pin: undefined,
            },
        });
    } catch (error: any) {
        console.error('Error updating profile:', error);
        return NextResponse.json(
            { error: 'Failed to update profile' },
            { status: 500 }
        );
    }
}

/**
 * DELETE /api/profiles/[id]
 * Delete profile
 */
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const { id } = await params;

        const profile = await prisma.profile.findUnique({
            where: { id },
        });

        if (!profile) {
            return NextResponse.json({ error: 'Profile not found' }, { status: 404 });
        }

        if (profile.userId !== user.id) {
            return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
        }

        if (profile.isPrimary) {
            return NextResponse.json(
                { error: 'Cannot delete primary profile' },
                { status: 400 }
            );
        }

        await prisma.profile.delete({
            where: { id },
        });

        return NextResponse.json({ message: 'Profile deleted successfully' });
    } catch (error: any) {
        console.error('Error deleting profile:', error);
        return NextResponse.json(
            { error: 'Failed to delete profile' },
            { status: 500 }
        );
    }
}

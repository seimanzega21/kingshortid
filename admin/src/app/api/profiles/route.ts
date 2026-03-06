import { NextRequest, NextResponse } from 'next/server';
import { getAuthUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';
import bcrypt from 'bcryptjs';

/**
 * GET /api/profiles
 * Get all profiles for current user
 */
export async function GET(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const profiles = await prisma.profile.findMany({
            where: { userId: user.id },
            orderBy: [
                { isPrimary: 'desc' },
                { createdAt: 'asc' },
            ],
            select: {
                id: true,
                name: true,
                avatar: true,
                isPrimary: true,
                ageRating: true,
                language: true,
                theme: true,
                autoPlay: true,
                createdAt: true,
                pin: true, // Just to check if exists, not the actual value
            },
        });

        // Hide actual PIN, just return boolean
        const profilesWithPinStatus = profiles.map(p => ({
            ...p,
            hasPin: !!p.pin,
            pin: undefined,
        }));

        return NextResponse.json({ profiles: profilesWithPinStatus });
    } catch (error: any) {
        console.error('Error fetching profiles:', error);
        return NextResponse.json(
            { error: 'Failed to fetch profiles' },
            { status: 500 }
        );
    }
}

/**
 * POST /api/profiles
 * Create new profile
 */
export async function POST(request: NextRequest) {
    try {
        const user = await getAuthUser(request);
        if (!user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const body = await request.json();
        const { name, avatar, ageRating, pin, language, theme } = body;

        if (!name) {
            return NextResponse.json(
                { error: 'Profile name is required' },
                { status: 400 }
            );
        }

        // Check profile limit (max 5 profiles per user)
        const profileCount = await prisma.profile.count({
            where: { userId: user.id },
        });

        if (profileCount >= 5) {
            return NextResponse.json(
                { error: 'Maximum 5 profiles allowed per account' },
                { status: 400 }
            );
        }

        // Hash PIN if provided
        const hashedPin = pin ? await bcrypt.hash(pin, 10) : null;

        // Create profile
        const profile = await prisma.profile.create({
            data: {
                userId: user.id,
                name,
                avatar: avatar || '👤',
                ageRating: ageRating || 'all',
                pin: hashedPin,
                language: language || 'id',
                theme: theme || 'dark',
                isPrimary: profileCount === 0, // First profile is primary
            },
        });

        return NextResponse.json({
            profile: {
                ...profile,
                hasPin: !!profile.pin,
                pin: undefined,
            },
        }, { status: 201 });
    } catch (error: any) {
        console.error('Error creating profile:', error);
        return NextResponse.json(
            { error: 'Failed to create profile' },
            { status: 500 }
        );
    }
}

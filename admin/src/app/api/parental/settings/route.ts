import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyAuth } from '@/lib/auth';
import bcrypt from 'bcryptjs';

type AgeRating = 'all' | '13+' | '16+' | '18+';

interface ParentalSettings {
    maxAgeRating: AgeRating;
    parentalControlsEnabled: boolean;
    restrictedGenres: string[];
    lockSettings: boolean;
}

// GET /api/parental/settings - Get parental control settings
export async function GET(request: NextRequest) {
    try {
        const user = await verifyAuth(request);
        if (!user) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        const userData = await prisma.user.findUnique({
            where: { id: user.id },
            select: { preferences: true },
        });

        const prefs = (userData?.preferences as any) || {};

        return NextResponse.json({
            hasPin: !!prefs.parentalPin,
            maxAgeRating: prefs.maxAgeRating || 'all',
            parentalControlsEnabled: prefs.parentalControlsEnabled || false,
            restrictedGenres: prefs.restrictedGenres || [],
            lockSettings: prefs.lockSettings || false,
        });
    } catch (error: any) {
        return NextResponse.json(
            { error: 'Failed to get settings' },
            { status: 500 }
        );
    }
}

// PUT /api/parental/settings - Update parental control settings
export async function PUT(request: NextRequest) {
    try {
        const user = await verifyAuth(request);
        if (!user) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        const { pin, settings } = await request.json();

        // Get current preferences
        const userData = await prisma.user.findUnique({
            where: { id: user.id },
            select: { preferences: true },
        });

        const prefs = (userData?.preferences as any) || {};

        // If parental controls are set, require PIN
        if (prefs.parentalPin) {
            if (!pin) {
                return NextResponse.json(
                    { error: 'PIN required to update settings' },
                    { status: 400 }
                );
            }

            const isValid = await bcrypt.compare(pin, prefs.parentalPin);
            if (!isValid) {
                return NextResponse.json(
                    { error: 'Invalid PIN' },
                    { status: 403 }
                );
            }
        }

        // Validate age rating
        const validRatings: AgeRating[] = ['all', '13+', '16+', '18+'];
        if (settings.maxAgeRating && !validRatings.includes(settings.maxAgeRating)) {
            return NextResponse.json(
                { error: 'Invalid age rating' },
                { status: 400 }
            );
        }

        // Update settings
        const updatedPrefs = {
            ...prefs,
            maxAgeRating: settings.maxAgeRating ?? prefs.maxAgeRating ?? 'all',
            parentalControlsEnabled: settings.parentalControlsEnabled ?? prefs.parentalControlsEnabled ?? false,
            restrictedGenres: settings.restrictedGenres ?? prefs.restrictedGenres ?? [],
            lockSettings: settings.lockSettings ?? prefs.lockSettings ?? false,
        };

        await prisma.user.update({
            where: { id: user.id },
            data: {
                preferences: updatedPrefs,
            },
        });

        return NextResponse.json({
            success: true,
            settings: {
                maxAgeRating: updatedPrefs.maxAgeRating,
                parentalControlsEnabled: updatedPrefs.parentalControlsEnabled,
                restrictedGenres: updatedPrefs.restrictedGenres,
                lockSettings: updatedPrefs.lockSettings,
            },
        });
    } catch (error: any) {
        console.error('Update settings error:', error);
        return NextResponse.json(
            { error: 'Failed to update settings' },
            { status: 500 }
        );
    }
}

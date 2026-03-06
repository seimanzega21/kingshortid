import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyAuth } from '@/lib/auth';
import bcrypt from 'bcryptjs';

// POST /api/parental/verify-pin - Verify parental control PIN
export async function POST(request: NextRequest) {
    try {
        const user = await verifyAuth(request);
        if (!user) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        const { pin } = await request.json();

        if (!pin || pin.length !== 4) {
            return NextResponse.json(
                { error: 'PIN must be 4 digits' },
                { status: 400 }
            );
        }

        // Get user's parental PIN
        const userData = await prisma.user.findUnique({
            where: { id: user.id },
            select: { preferences: true },
        });

        const prefs = (userData?.preferences as any) || {};

        if (!prefs.parentalPin) {
            return NextResponse.json(
                { error: 'Parental controls not set up' },
                { status: 404 }
            );
        }

        // Verify PIN
        const isValid = await bcrypt.compare(pin, prefs.parentalPin);

        if (!isValid) {
            return NextResponse.json(
                { error: 'Invalid PIN', valid: false },
                { status: 403 }
            );
        }

        return NextResponse.json({
            valid: true,
            settings: {
                maxAgeRating: prefs.maxAgeRating || 'all',
                parentalControlsEnabled: prefs.parentalControlsEnabled || false,
                restrictedGenres: prefs.restrictedGenres || [],
            },
        });
    } catch (error: any) {
        console.error('Verify PIN error:', error);
        return NextResponse.json(
            { error: 'Failed to verify PIN' },
            { status: 500 }
        );
    }
}

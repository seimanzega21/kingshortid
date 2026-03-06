import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyAuth } from '@/lib/auth';
import bcrypt from 'bcryptjs';

// POST /api/parental/set-pin - Set parental control PIN
export async function POST(request: NextRequest) {
    try {
        const user = await verifyAuth(request);
        if (!user) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        const { pin, currentPin } = await request.json();

        if (!pin || pin.length !== 4 || !/^\d{4}$/.test(pin)) {
            return NextResponse.json(
                { error: 'PIN must be 4 digits' },
                { status: 400 }
            );
        }

        // Check if user already has a parental PIN
        const existingSettings = await prisma.user.findUnique({
            where: { id: user.id },
            select: { preferences: true },
        });

        const prefs = (existingSettings?.preferences as any) || {};

        // If updating existing PIN, verify current PIN
        if (prefs.parentalPin) {
            if (!currentPin) {
                return NextResponse.json(
                    { error: 'Current PIN required to change PIN' },
                    { status: 400 }
                );
            }

            const isValid = await bcrypt.compare(currentPin, prefs.parentalPin);
            if (!isValid) {
                return NextResponse.json(
                    { error: 'Current PIN is incorrect' },
                    { status: 403 }
                );
            }
        }

        // Hash and save new PIN
        const hashedPin = await bcrypt.hash(pin, 10);

        await prisma.user.update({
            where: { id: user.id },
            data: {
                preferences: {
                    ...prefs,
                    parentalPin: hashedPin,
                    parentalControlsEnabled: true,
                    maxAgeRating: prefs.maxAgeRating || 'all',
                },
            },
        });

        return NextResponse.json({
            success: true,
            message: 'Parental PIN set successfully',
        });
    } catch (error: any) {
        console.error('Set PIN error:', error);
        return NextResponse.json(
            { error: 'Failed to set PIN' },
            { status: 500 }
        );
    }
}

// DELETE /api/parental/set-pin - Remove parental PIN
export async function DELETE(request: NextRequest) {
    try {
        const user = await verifyAuth(request);
        if (!user) {
            return NextResponse.json(
                { error: 'Unauthorized' },
                { status: 401 }
            );
        }

        const { pin } = await request.json();

        // Verify current PIN
        const existingSettings = await prisma.user.findUnique({
            where: { id: user.id },
            select: { preferences: true },
        });

        const prefs = (existingSettings?.preferences as any) || {};

        if (prefs.parentalPin) {
            if (!pin) {
                return NextResponse.json(
                    { error: 'Current PIN required' },
                    { status: 400 }
                );
            }

            const isValid = await bcrypt.compare(pin, prefs.parentalPin);
            if (!isValid) {
                return NextResponse.json(
                    { error: 'PIN is incorrect' },
                    { status: 403 }
                );
            }
        }

        // Remove PIN and disable parental controls
        await prisma.user.update({
            where: { id: user.id },
            data: {
                preferences: {
                    ...prefs,
                    parentalPin: null,
                    parentalControlsEnabled: false,
                },
            },
        });

        return NextResponse.json({
            success: true,
            message: 'Parental controls disabled',
        });
    } catch (error: any) {
        return NextResponse.json(
            { error: 'Failed to remove PIN' },
            { status: 500 }
        );
    }
}

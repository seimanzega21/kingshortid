import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(
    request: NextRequest
) {
    try {
        const body = await request.json();
        const { email } = body;

        if (!email) {
            return NextResponse.json({ message: 'Email is required' }, { status: 400 });
        }

        console.log(`🚀 Resetting coins for ${email} directly via Admin SQL...`);

        // Use Raw SQL to bypass outdated Prisma schema and ensure purchased_coins is also reset
        // We use prisma.$executeRaw because the schema might be missing columns
        await prisma.$executeRawUnsafe(
            `UPDATE "User" SET coins = 0, "purchased_coins" = 0, "updatedAt" = NOW() WHERE email = $1`,
            email
        );

        return NextResponse.json({ success: true, message: `Coins for ${email} have been reset to 0.` });
    } catch (error: any) {
        console.error('Reset coins error:', error);
        return NextResponse.json({ message: error.message || 'Failed to reset coins' }, { status: 500 });
    }
}

import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { getAuthUser } from '@/lib/auth';

// GET /api/episodes/[id]/stream
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        // 1. Get Episode Details
        const episode = await prisma.episode.findUnique({
            where: { id },
            select: {
                id: true,
                isVip: true,
                videoUrl: true,
                coinPrice: true
            }
        });

        if (!episode) return NextResponse.json({ message: 'Episode not found' }, { status: 404 });

        // 2. If FREE, return immediately
        if (!episode.isVip) {
            return NextResponse.json({ url: episode.videoUrl });
        }

        // 3. If VIP, Check Auth & Permissions
        const user = await getAuthUser(request);
        if (!user) {
            // Unauthenticated users cannot watch VIP
            return NextResponse.json({ message: 'Auth required for VIP' }, { status: 401 });
        }

        const dbUser = await prisma.user.findUnique({
            where: { id: user.id },
            select: { vipStatus: true, vipExpiry: true }
        });

        // 3a. Check User VIP Subscription
        if (dbUser?.vipStatus && dbUser.vipExpiry && new Date(dbUser.vipExpiry) > new Date()) {
            return NextResponse.json({ url: episode.videoUrl, access: 'vip_sub' });
        }

        // 3b. Check if Purchased Individually
        // Check CoinTransaction for 'spend' on this reference
        const purchase = await prisma.coinTransaction.findFirst({
            where: {
                userId: user.id,
                reference: id, // We used episodeId as reference in spend API
                type: 'spend'
            }
        });

        if (purchase) {
            return NextResponse.json({ url: episode.videoUrl, access: 'purchased' });
        }

        // 4. Access Denied
        return NextResponse.json({
            message: 'Payment required',
            price: episode.coinPrice,
            locked: true
        }, { status: 403 });

    } catch (error) {
        return NextResponse.json({ message: 'Error' }, { status: 500 });
    }
}

import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/auth';
import {
    sendWelcomeEmail,
    sendNewEpisodeEmail,
    sendWeeklyDigestEmail,
    sendPasswordResetEmail,
} from '@/lib/email';

/**
 * POST /api/notifications/email/send
 * Send email notification (Admin only)
 */
export async function POST(request: NextRequest) {
    try {
        await requireAdmin(request);

        const body = await request.json();
        const { type, to, data } = body;

        if (!type || !to) {
            return NextResponse.json(
                { error: 'Type and recipient email are required' },
                { status: 400 }
            );
        }

        let result;

        switch (type) {
            case 'welcome':
                result = await sendWelcomeEmail(to, data.name);
                break;

            case 'new_episode':
                result = await sendNewEpisodeEmail(
                    to,
                    data.dramaTitle,
                    data.episodeNumber,
                    data.episodeTitle
                );
                break;

            case 'weekly_digest':
                result = await sendWeeklyDigestEmail(to, data.name, data.stats);
                break;

            case 'password_reset':
                result = await sendPasswordResetEmail(to, data.resetToken);
                break;

            default:
                return NextResponse.json(
                    { error: 'Invalid email type' },
                    { status: 400 }
                );
        }

        if (!result.success) {
            return NextResponse.json(
                { error: result.error || 'Failed to send email' },
                { status: 500 }
            );
        }

        return NextResponse.json({
            message: 'Email sent successfully',
            id: result.id,
        });
    } catch (error: any) {
        console.error('Error sending email:', error);
        return NextResponse.json(
            { error: 'Failed to send email' },
            { status: 500 }
        );
    }
}

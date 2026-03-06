import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { verifyAuth, verifyAdmin } from '@/lib/auth';

// GET /api/subtitles - Get subtitles for an episode
export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const episodeId = searchParams.get('episodeId');
        const dramaId = searchParams.get('dramaId');

        if (!episodeId && !dramaId) {
            return NextResponse.json(
                { error: 'episodeId or dramaId required' },
                { status: 400 }
            );
        }

        // Since Subtitle model might not exist yet, return mock data
        // In production, you would query: prisma.subtitle.findMany(...)

        const mockSubtitles = [
            {
                id: 'sub_id_1',
                episodeId: episodeId || '',
                language: 'id',
                label: 'Bahasa Indonesia',
                url: '/subtitles/episode-1-id.srt',
                isDefault: true,
                createdAt: new Date().toISOString(),
            },
            {
                id: 'sub_id_2',
                episodeId: episodeId || '',
                language: 'en',
                label: 'English',
                url: '/subtitles/episode-1-en.srt',
                isDefault: false,
                createdAt: new Date().toISOString(),
            },
        ];

        // Check if we have real subtitles in database
        // const subtitles = await prisma.subtitle.findMany({
        //   where: episodeId ? { episodeId } : { episode: { dramaId } },
        //   orderBy: { language: 'asc' },
        // });

        return NextResponse.json({
            subtitles: episodeId ? mockSubtitles : [],
            count: episodeId ? mockSubtitles.length : 0,
        });
    } catch (error: any) {
        console.error('Get subtitles error:', error);
        return NextResponse.json(
            { error: 'Failed to get subtitles' },
            { status: 500 }
        );
    }
}

// POST /api/subtitles - Upload subtitle (Admin only)
export async function POST(request: NextRequest) {
    try {
        const isAdmin = await verifyAdmin(request);
        if (!isAdmin) {
            return NextResponse.json(
                { error: 'Admin access required' },
                { status: 403 }
            );
        }

        const formData = await request.formData();
        const file = formData.get('file') as File | null;
        const episodeId = formData.get('episodeId') as string;
        const language = formData.get('language') as string;
        const label = formData.get('label') as string;

        if (!file || !episodeId || !language) {
            return NextResponse.json(
                { error: 'File, episodeId, and language are required' },
                { status: 400 }
            );
        }

        // Validate file type
        const validExtensions = ['.srt', '.vtt'];
        const fileName = file.name.toLowerCase();
        const isValidFile = validExtensions.some(ext => fileName.endsWith(ext));

        if (!isValidFile) {
            return NextResponse.json(
                { error: 'Only .srt and .vtt files are allowed' },
                { status: 400 }
            );
        }

        // Verify episode exists
        const episode = await prisma.episode.findUnique({
            where: { id: episodeId },
            select: { id: true, dramaId: true },
        });

        if (!episode) {
            return NextResponse.json(
                { error: 'Episode not found' },
                { status: 404 }
            );
        }

        // Read file content
        const content = await file.text();

        // Validate SRT/VTT content
        if (!isValidSubtitleContent(content)) {
            return NextResponse.json(
                { error: 'Invalid subtitle file format' },
                { status: 400 }
            );
        }

        // In production, upload to storage and save to database
        // For now, return success response
        const subtitle = {
            id: `sub_${Date.now()}`,
            episodeId,
            language,
            label: label || getLanguageLabel(language),
            url: `/subtitles/${episodeId}-${language}.srt`,
            isDefault: language === 'id',
            createdAt: new Date().toISOString(),
        };

        // await prisma.subtitle.create({ data: subtitle });

        return NextResponse.json({
            success: true,
            subtitle,
        });
    } catch (error: any) {
        console.error('Upload subtitle error:', error);
        return NextResponse.json(
            { error: 'Failed to upload subtitle' },
            { status: 500 }
        );
    }
}

// DELETE /api/subtitles - Delete subtitle (Admin only)
export async function DELETE(request: NextRequest) {
    try {
        const isAdmin = await verifyAdmin(request);
        if (!isAdmin) {
            return NextResponse.json(
                { error: 'Admin access required' },
                { status: 403 }
            );
        }

        const { searchParams } = new URL(request.url);
        const subtitleId = searchParams.get('id');

        if (!subtitleId) {
            return NextResponse.json(
                { error: 'Subtitle ID required' },
                { status: 400 }
            );
        }

        // await prisma.subtitle.delete({ where: { id: subtitleId } });

        return NextResponse.json({
            success: true,
            message: 'Subtitle deleted',
        });
    } catch (error: any) {
        return NextResponse.json(
            { error: 'Failed to delete subtitle' },
            { status: 500 }
        );
    }
}

// Helper functions
function isValidSubtitleContent(content: string): boolean {
    const trimmed = content.trim();

    // Check for WebVTT
    if (trimmed.startsWith('WEBVTT')) {
        return true;
    }

    // Check for SRT (should start with a number)
    if (/^\d+\s*\n/.test(trimmed)) {
        // Check for timing pattern
        return /\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}/.test(content);
    }

    return false;
}

function getLanguageLabel(language: string): string {
    const labels: Record<string, string> = {
        'id': 'Bahasa Indonesia',
        'en': 'English',
        'ko': '한국어 (Korean)',
        'zh': '中文 (Chinese)',
        'ja': '日本語 (Japanese)',
        'th': 'ไทย (Thai)',
        'vi': 'Tiếng Việt (Vietnamese)',
        'ms': 'Bahasa Melayu',
        'tl': 'Filipino',
    };
    return labels[language.toLowerCase()] || language;
}

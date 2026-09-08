import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { deleteR2FilesByPrefix, r2Client, R2_BUCKET } from '@/lib/r2-helper';
import { DeleteObjectCommand } from '@aws-sdk/client-s3';

// GET /api/dramas/[id]
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;

        const drama = await prisma.drama.findUnique({
            where: { id },
            include: {
                _count: {
                    select: {
                        episodes: true,
                        favorites: true,
                        watchlist: true,
                        comments: true,
                        reviews: true,
                    },
                },
            },
        });

        if (!drama) {
            return NextResponse.json(
                { message: 'Drama not found' },
                { status: 404 }
            );
        }

        // Fetch episodes using raw query (workaround for Prisma include issue)
        const episodes = await prisma.$queryRaw`
            SELECT id, "episodeNumber", title, "videoUrl", duration, views, 
                   "isVip", "isActive", "createdAt"
            FROM "Episode" 
            WHERE "dramaId" = ${id}
            ORDER BY "episodeNumber" ASC
        `;

        return NextResponse.json({ ...drama, episodes });
    } catch (error) {
        console.error('Get drama error:', error);
        return NextResponse.json(
            { message: 'Failed to get drama' },
            { status: 500 }
        );
    }
}

// PATCH /api/dramas/[id]
export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const body = await request.json();

        const allowedFields = [
            'title', 'description', 'cover', 'banner', 'genres', 'tagList',
            'status', 'isVip', 'isFeatured', 'isActive', 'ageRating',
            'director', 'cast', 'country', 'language', 'totalEpisodes',
            'rating', 'views',
        ];

        const updateData: any = {};
        for (const field of allowedFields) {
            if (body[field] !== undefined) {
                updateData[field] = body[field];
            }
        }

        // Auto-sync banner when cover is updated but banner not explicitly set
        if (updateData.cover && !updateData.banner) {
            updateData.banner = updateData.cover;
        }

        const existing = await prisma.drama.findUnique({ where: { id }, select: { isActive: true } });
        if (!existing) {
            return NextResponse.json({ message: 'Drama not found' }, { status: 404 });
        }

        if (updateData.isActive === true && existing.isActive === false) {
            updateData.createdAt = new Date();
        }

        const drama = await prisma.drama.update({
            where: { id },
            data: updateData,
        });

        return NextResponse.json(drama);
    } catch (error: any) {
        console.error('Update drama error:', error);
        if (error.code === 'P2025') {
            return NextResponse.json(
                { message: 'Drama not found' },
                { status: 404 }
            );
        }
        return NextResponse.json(
            { message: 'Failed to update drama' },
            { status: 500 }
        );
    }
}

// DELETE /api/dramas/[id]
export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const { searchParams } = new URL(request.url);
        const deleteFromR2 = searchParams.get('deleteFromR2') === 'true';

        // 1. Ambil detail drama dan episodenya sebelum dihapus dari DB
        const drama = await prisma.drama.findUnique({
            where: { id },
            include: { episodes: true }
        });

        if (!drama) {
            return NextResponse.json({ message: 'Drama not found' }, { status: 404 });
        }

        // 2. Jika user mencentang 'Hapus juga file dari Server (R2)', bersihkan R2
        if (deleteFromR2) {
            try {
                const deletedKeys = new Set<string>();

                // A. Deteksi prefix folder dari video episode pertama (contoh: "dramas/netshort/slug/" atau "melolov3/slug/")
                const sampleVideo = drama.episodes?.find(e => e.videoUrl && e.videoUrl.includes('stream.shortlovers.id'))?.videoUrl;
                if (sampleVideo) {
                    try {
                        const parsed = new URL(sampleVideo);
                        const parts = parsed.pathname.replace(/^\//, '').split('/');
                        if (parts.length >= 2) {
                            const folderPrefix = `${parts[0]}/${parts[1]}/`;
                            const deletedCount = await deleteR2FilesByPrefix(folderPrefix);
                            console.log(`[Admin DELETE] Deleted ${deletedCount} files from R2 folder: ${folderPrefix}`);
                        }
                    } catch (e) {
                        console.error('[Admin DELETE] Error parsing sample video URL:', e);
                    }
                }

                // B. Hapus file cover jika tersimpan di R2 (misal: "dramas/covers/slug_cover_hq.jpg")
                if (drama.cover && drama.cover.includes('stream.shortlovers.id')) {
                    try {
                        const coverPath = new URL(drama.cover).pathname.replace(/^\//, '');
                        await r2Client.send(new DeleteObjectCommand({
                            Bucket: R2_BUCKET,
                            Key: coverPath
                        })).catch(() => {});
                    } catch { }
                }

                // C. Hapus banner jika ada di R2
                if (drama.banner && drama.banner.includes('stream.shortlovers.id')) {
                    try {
                        const bannerPath = new URL(drama.banner).pathname.replace(/^\//, '');
                        await r2Client.send(new DeleteObjectCommand({
                            Bucket: R2_BUCKET,
                            Key: bannerPath
                        })).catch(() => {});
                    } catch { }
                }
            } catch (r2Err) {
                console.error('[Admin DELETE] Error cleaning R2 files:', r2Err);
            }
        }

        // 3. Hapus relasi episode dan drama dari Database
        await prisma.episode.deleteMany({ where: { dramaId: id } });
        await prisma.drama.delete({ where: { id } });

        return NextResponse.json({
            message: `Drama "${drama.title}" berhasil dihapus${deleteFromR2 ? ' beserta seluruh file di Cloudflare R2' : ''}`
        });
    } catch (error: any) {
        console.error('Delete drama error:', error);
        if (error.code === 'P2025') {
            return NextResponse.json(
                { message: 'Drama not found' },
                { status: 404 }
            );
        }
        return NextResponse.json(
            { message: 'Failed to delete drama' },
            { status: 500 }
        );
    }
}

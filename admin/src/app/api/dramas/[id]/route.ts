import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';
import { deleteR2FilesByPrefix, deleteR2Objects, PROTECTED_R2_PREFIXES } from '@/lib/r2-helper';

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
            'rating', 'views', 'likes',
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

        const res = NextResponse.json(drama);
        res.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
        return res;
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

        // 1. Ambil detail drama dan seluruh relasi episodenya sebelum dihapus dari DB
        const drama = await prisma.drama.findUnique({
            where: { id },
            include: {
                episodes: {
                    select: {
                        id: true,
                        videoUrl: true,
                        videoUrl540p: true,
                        thumbnail: true,
                    }
                }
            }
        });

        if (!drama) {
            return NextResponse.json({ message: 'Drama not found' }, { status: 404 });
        }

        // 2. Jika user mencentang 'Hapus juga file dari Server (R2)', bersihkan R2 dengan verifikasi keamanan ketat
        let deletedR2Count = 0;
        if (deleteFromR2) {
            try {
                // Helper untuk mengekstrak path object R2 dari full URL
                const extractR2Key = (url?: string | null): string | null => {
                    if (!url) return null;
                    try {
                        if (url.includes('stream.shortlovers.id') || url.includes('.r2.cloudflarestorage.com') || url.includes('.r2.dev')) {
                            const parsed = new URL(url);
                            return decodeURIComponent(parsed.pathname.replace(/^\/+/, ''));
                        }
                    } catch {}
                    return null;
                };

                // Kumpulkan semua keys spesifik milik drama ini
                const candidateKeys = new Set<string>();

                const coverKey = extractR2Key(drama.cover);
                if (coverKey) candidateKeys.add(coverKey);

                const bannerKey = extractR2Key(drama.banner);
                if (bannerKey) candidateKeys.add(bannerKey);

                for (const ep of drama.episodes) {
                    const vKey = extractR2Key(ep.videoUrl);
                    if (vKey) candidateKeys.add(vKey);

                    const v540Key = extractR2Key(ep.videoUrl540p);
                    if (v540Key) candidateKeys.add(v540Key);

                    const tKey = extractR2Key(ep.thumbnail);
                    if (tKey) candidateKeys.add(tKey);
                }

                // Cek subtitle episode drama ini
                try {
                    const subs = await prisma.subtitle.findMany({
                        where: { episode: { dramaId: id } },
                        select: { url: true }
                    });
                    for (const sub of subs) {
                        const subKey = extractR2Key(sub.url);
                        if (subKey) candidateKeys.add(subKey);
                    }
                } catch {}

                // FILTER KEAMANAN: HANYA hapus file yang TIDAK dipakai oleh drama atau episode lain!
                const keysToDelete: string[] = [];
                for (const key of Array.from(candidateKeys)) {
                    // Cek apakah key ini masih dipakai sebagai cover atau banner di drama lain
                    const usedInOtherDrama = await prisma.drama.findFirst({
                        where: {
                            id: { not: id },
                            OR: [
                                { cover: { contains: key } },
                                { banner: { contains: key } },
                            ]
                        },
                        select: { id: true }
                    });

                    if (usedInOtherDrama) {
                        console.log(`[R2 SAFE PRESERVE] File "${key}" dipertahankan di R2 karena masih digunakan oleh drama ID ${usedInOtherDrama.id}`);
                        continue;
                    }

                    // Cek apakah key ini masih dipakai sebagai video/thumbnail di episode drama lain
                    const usedInOtherEpisode = await prisma.episode.findFirst({
                        where: {
                            dramaId: { not: id },
                            OR: [
                                { videoUrl: { contains: key } },
                                { videoUrl540p: { contains: key } },
                                { thumbnail: { contains: key } },
                            ]
                        },
                        select: { id: true }
                    });

                    if (usedInOtherEpisode) {
                        console.log(`[R2 SAFE PRESERVE] File "${key}" dipertahankan di R2 karena masih digunakan oleh episode ID ${usedInOtherEpisode.id}`);
                        continue;
                    }

                    // Aman dihapus karena eksklusif hanya milik drama ini
                    keysToDelete.push(key);
                }

                if (keysToDelete.length > 0) {
                    deletedR2Count = await deleteR2Objects(keysToDelete);
                    console.log(`[Admin DELETE] Berhasil menghapus ${deletedR2Count} file eksklusif dari R2 untuk drama: ${drama.title}`);
                }

                // PEMBERSIHAN FOLDER RESIDU (hanya jika folder benar-benar unik milik drama ini dan tidak dipakai siapapun)
                const sampleVideo = drama.episodes?.find(e => e.videoUrl && e.videoUrl.includes('stream.shortlovers.id'))?.videoUrl;
                if (sampleVideo) {
                    try {
                        const parsed = new URL(sampleVideo);
                        const parts = parsed.pathname.replace(/^\/+/, '').split('/');
                        // Syarat mutlak: minimal 3 segmen (misal: "dramas/netshort/slug/ep.mp4" -> kedalaman folder minimal 2 segmen)
                        if (parts.length >= 3) {
                            const folderPrefix = parts.slice(0, -1).join('/') + '/';

                            // Tolak jika folder berada dalam daftar prefix bersama/kritis (misal "dramas/covers/")
                            const isShared = PROTECTED_R2_PREFIXES.some(p => p && (folderPrefix === p || folderPrefix.startsWith(p) && p.endsWith('/covers/')));

                            if (!isShared) {
                                // Pastikan TIDAK ADA drama lain yang menggunakan folder ini
                                const otherDramaInFolder = await prisma.drama.findFirst({
                                    where: {
                                        id: { not: id },
                                        OR: [
                                            { cover: { contains: folderPrefix } },
                                            { banner: { contains: folderPrefix } }
                                        ]
                                    },
                                    select: { id: true }
                                });

                                const otherEpInFolder = await prisma.episode.findFirst({
                                    where: {
                                        dramaId: { not: id },
                                        OR: [
                                            { videoUrl: { contains: folderPrefix } },
                                            { videoUrl540p: { contains: folderPrefix } },
                                            { thumbnail: { contains: folderPrefix } }
                                        ]
                                    },
                                    select: { id: true }
                                });

                                if (!otherDramaInFolder && !otherEpInFolder) {
                                    const extraDeleted = await deleteR2FilesByPrefix(folderPrefix);
                                    deletedR2Count += extraDeleted;
                                    console.log(`[Admin DELETE] Folder dedicated bersih: ${folderPrefix} (${extraDeleted} file residu dihapus)`);
                                } else {
                                    console.log(`[R2 SAFE] Melewati pembersihan folder prefix "${folderPrefix}" karena digunakan oleh drama/episode lain.`);
                                }
                            }
                        }
                    } catch (e) {
                        console.error('[Admin DELETE] Error checking folder prefix:', e);
                    }
                }
            } catch (r2Err) {
                console.error('[Admin DELETE] Error cleaning R2 files:', r2Err);
            }
        }

        // 3. Hapus relasi episode, subtitles, dan drama dari Database
        await prisma.subtitle.deleteMany({ where: { episode: { dramaId: id } } }).catch(() => {});
        await prisma.episode.deleteMany({ where: { dramaId: id } });
        await prisma.drama.delete({ where: { id } });

        return NextResponse.json({
            message: `Drama "${drama.title}" berhasil dihapus${deleteFromR2 ? ` beserta ${deletedR2Count} file di Cloudflare R2 (file yang dipakai drama lain tetap aman)` : ''}`
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

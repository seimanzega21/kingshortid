import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// POST /api/dramas/fix-genres — Auto-classify dramas with generic 'Drama' genre
export async function POST(request: NextRequest) {
    try {
        const dramas = await prisma.drama.findMany({
            where: {
                isActive: true,
                genres: { equals: ['Drama'] },
            },
            select: { id: true, title: true, description: true, genres: true },
        });

        // Keyword-based genre mapping (Indonesian)
        const genreMap: Record<string, string[]> = {
            'Romantis': ['cinta', 'romantis', 'jatuh cinta', 'pernikahan', 'nikah', 'menikah', 'pacar', 'suami', 'istri', 'percintaan', 'hati', 'pasangan', 'hubungan', 'kekasih', 'mantan', 'tunangan', 'love'],
            'Aksi': ['aksi', 'bertarung', 'perang', 'pertempuran', 'seni bela diri', 'silat', 'kungfu', 'petarung', 'dewa perang', 'penguasa', 'terkuat', 'tertinggi', 'level dewa', 'kultivator'],
            'Fantasi': ['fantasi', 'dewa', 'dewi', 'setan', 'iblis', 'jiwa', 'reinkarnasi', 'sihir', 'dunia lain', 'naga', 'giok', 'kultivat', 'abadi', 'immortal', 'spiritual'],
            'Bisnis': ['bisnis', 'ceo', 'perusahaan', 'kontrak', 'miliar', 'kaya', 'konglomerat', 'jutawan', 'milliar', 'bos', 'presdir', 'direktur', 'saham', 'warisan', 'korporasi'],
            'Keluarga': ['keluarga', 'ibu', 'ayah', 'anak', 'mama', 'papa', 'bayi', 'hamil', 'kembar', 'mertua', 'menantu', 'adik', 'kakak', 'saudara', 'pengasuh'],
            'Misteri': ['misteri', 'rahasia', 'tersembunyi', 'identitas', 'menyamar', 'penyamaran', 'terungkap', 'detektif'],
            'Balas Dendam': ['balas dendam', 'membalas', 'dendam', 'dikhianati', 'dibuang', 'diusir', 'dihina', 'penghinaan', 'serangan balik', 'bangkit'],
            'Komedi': ['komedi', 'lucu', 'humor', 'kocak', 'ngakak', 'gokil'],
        };

        let updated = 0;
        const results: Array<{ id: string; title: string; oldGenres: string[]; newGenres: string[] }> = [];

        for (const drama of dramas) {
            const text = `${drama.title} ${drama.description || ''}`.toLowerCase();
            const matchedGenres: string[] = ['Drama']; // Keep 'Drama' as base

            for (const [genre, keywords] of Object.entries(genreMap)) {
                if (keywords.some(kw => text.includes(kw))) {
                    matchedGenres.push(genre);
                }
            }

            // Only update if we found additional genres
            if (matchedGenres.length > 1) {
                await prisma.drama.update({
                    where: { id: drama.id },
                    data: { genres: matchedGenres },
                });
                updated++;
                results.push({
                    id: drama.id,
                    title: drama.title,
                    oldGenres: drama.genres as string[],
                    newGenres: matchedGenres,
                });
            }
        }

        return NextResponse.json({
            message: `${updated} dramas updated out of ${dramas.length} generic`,
            updated,
            total: dramas.length,
            remaining: dramas.length - updated,
            results: results.slice(0, 20), // Show first 20
        });
    } catch (error) {
        console.error('Fix genres error:', error);
        return NextResponse.json({ message: 'Failed to fix genres' }, { status: 500 });
    }
}

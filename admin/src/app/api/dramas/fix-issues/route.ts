import { NextRequest, NextResponse } from 'next/server';
import prisma from '@/lib/prisma';

// POST /api/dramas/fix-issues — Auto-fix Bad Desc + Genre Generic in one shot
export async function POST(request: NextRequest) {
    try {
        const results = {
            descFixed: 0,
            genreFixed: 0,
            details: [] as Array<{ title: string; fixed: string[] }>,
        };

        // ===== 1. Fix Bad Descriptions =====
        // Find dramas where description is empty, equals title, or < 10 chars
        const allDramas = await prisma.drama.findMany({
            select: { id: true, title: true, description: true, genres: true },
        });

        for (const drama of allDramas) {
            const fixes: string[] = [];

            // Fix bad description
            const desc = drama.description || '';
            if (!desc || desc === drama.title || desc.length < 10) {
                const newDesc = generateDescription(drama.title, drama.genres as string[]);
                await prisma.drama.update({
                    where: { id: drama.id },
                    data: { description: newDesc },
                });
                results.descFixed++;
                fixes.push(`desc: "${desc}" → "${newDesc}"`);
            }

            // Fix generic genre
            const genres = drama.genres as string[];
            if (!genres || genres.length === 0 || (genres.length === 1 && genres[0] === 'Drama')) {
                const newGenres = classifyGenre(drama.title, drama.description || '');
                await prisma.drama.update({
                    where: { id: drama.id },
                    data: { genres: newGenres },
                });
                results.genreFixed++;
                fixes.push(`genres: [${genres?.join(',')}] → [${newGenres.join(',')}]`);
            }

            if (fixes.length > 0) {
                results.details.push({ title: drama.title, fixed: fixes });
            }
        }

        return NextResponse.json({
            message: `Fixed ${results.descFixed} descriptions, ${results.genreFixed} genres`,
            ...results,
        });
    } catch (error) {
        console.error('Fix issues error:', error);
        return NextResponse.json({ message: 'Failed to fix issues' }, { status: 500 });
    }
}

// Generate a description based on title keywords
function generateDescription(title: string, genres: string[]): string {
    const t = title.toLowerCase();
    const genreStr = genres?.filter(g => g !== 'Drama').join(', ') || '';

    // Title-specific descriptions
    const titleDescMap: Record<string, string> = {
        'anak magang ternyata istri ceo': 'Kisah seorang anak magang yang tak menyangka bahwa dirinya ternyata adalah istri sang CEO perusahaan. Perjalanan cinta yang penuh kejutan dan intrik kantor.',
        'dewa judi era 90 an': 'Di era 90-an, seorang legenda judi berusaha bertahan dan menguasai dunia perjudian. Aksi, strategi, dan pertaruhan hidup yang menegangkan.',
        'mafia yang kucintai': 'Kisah cinta yang terlarang antara seorang wanita biasa dan pemimpin mafia yang paling ditakuti. Di antara bahaya dan perasaan, ia harus membuat pilihan.',
        'planet yang mengembara': 'Ketika bumi terancam kehancuran, umat manusia harus bersatu untuk menyelamatkan peradaban di luar angkasa. Petualangan epik penuh aksi dan emosi.',
        'putri hoki sang jenderal': 'Seorang putri yang membawa keberuntungan bagi sang jenderal. Kisah peperangan, takdir, dan cinta yang mengubah sejarah kerajaan.',
        'saat dia pergi segalanya hancur': 'Kepergian seseorang yang dicintai membuat segalanya berantakan. Kisah tentang kehilangan, perjuangan bangkit, dan menemukan kembali makna hidup.',
        'saat dia pergi, segalanya hancur': 'Ketika orang yang paling berharga pergi, dunia terasa runtuh. Drama emosional tentang kehilangan, pengkhianatan, dan kekuatan untuk bangkit kembali.',
    };

    // Check exact title match first
    const exactDesc = titleDescMap[t];
    if (exactDesc) return exactDesc;

    // Fallback: generate from title patterns
    if (t.includes('ceo') || t.includes('presdir') || t.includes('bos')) {
        return `Kisah drama di dunia korporasi yang penuh intrik. ${title} menghadirkan cerita tentang kekuasaan, cinta, dan ambisi.`;
    }
    if (t.includes('mafia') || t.includes('gangster')) {
        return `Dunia gelap mafia menjadi latar cerita yang menegangkan. ${title} mengisahkan tentang kesetiaan, pengkhianatan, dan cinta di tengah bahaya.`;
    }
    if (t.includes('dewa') || t.includes('dewi') || t.includes('immortal')) {
        return `Petualangan fantasi yang epik di dunia para dewa. ${title} menceritakan perjuangan untuk meraih kekuatan tertinggi dan melindungi yang dicintai.`;
    }
    if (t.includes('jenderal') || t.includes('perang') || t.includes('raja')) {
        return `Kisah kepahlawanan dan strategi perang yang mengagumkan. ${title} menghadirkan aksi, kesetiaan, dan pengorbanan di medan pertempuran.`;
    }

    // Generic fallback
    return `${title} — serial drama yang menghadirkan kisah menarik penuh intrik, emosi, dan kejutan. Saksikan perjalanan karakter yang penuh liku dan tak terduga.`;
}

// Classify genre based on title keywords
function classifyGenre(title: string, description: string): string[] {
    const text = `${title} ${description}`.toLowerCase();
    const genres: string[] = ['Drama'];

    const genreMap: Record<string, string[]> = {
        'Romantis': ['cinta', 'romantis', 'pacar', 'suami', 'istri', 'nikah', 'menikah', 'kekasih', 'mantan', 'love', 'hati', 'percintaan', 'tunangan'],
        'Aksi': ['aksi', 'bertarung', 'perang', 'pertempuran', 'bela diri', 'silat', 'kungfu', 'petarung', 'terkuat', 'jenderal', 'prajurit'],
        'Fantasi': ['fantasi', 'dewa', 'dewi', 'setan', 'iblis', 'sihir', 'dunia lain', 'naga', 'giok', 'kultivat', 'abadi', 'immortal', 'planet', 'luar angkasa'],
        'Bisnis': ['bisnis', 'ceo', 'perusahaan', 'kontrak', 'miliar', 'kaya', 'konglomerat', 'milliar', 'bos', 'presdir', 'direktur', 'saham', 'warisan', 'magang', 'korporasi', 'kantor'],
        'Keluarga': ['keluarga', 'ibu', 'ayah', 'anak', 'bayi', 'hamil', 'kembar', 'mertua', 'menantu', 'saudara', 'pengasuh', 'putri', 'putra'],
        'Misteri': ['misteri', 'rahasia', 'tersembunyi', 'identitas', 'menyamar', 'terungkap', 'detektif'],
        'Balas Dendam': ['balas dendam', 'membalas', 'dendam', 'dikhianati', 'dibuang', 'diusir', 'dihina', 'serangan balik', 'bangkit', 'hancur'],
        'Komedi': ['komedi', 'lucu', 'humor', 'kocak', 'hoki'],
        'Sci-Fi': ['planet', 'luar angkasa', 'mengembara', 'teknologi', 'masa depan'],
        'Kriminal': ['mafia', 'gangster', 'judi', 'kriminal', 'penjahat', 'kejahatan'],
    };

    for (const [genre, keywords] of Object.entries(genreMap)) {
        if (keywords.some(kw => text.includes(kw))) {
            genres.push(genre);
        }
    }

    // If still only 'Drama', add based on general tone
    if (genres.length === 1) {
        genres.push('Kehidupan');
    }

    return genres;
}

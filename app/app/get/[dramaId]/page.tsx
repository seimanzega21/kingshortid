import { Metadata } from 'next';

interface Drama {
    id: string;
    title: string;
    description: string;
    cover: string;
    genre: string[];
    totalEpisodes: number;
    views: number;
}

interface Props {
    params: Promise<{ dramaId: string }>;
}

async function getDrama(dramaId: string): Promise<Drama | null> {
    try {
        const res = await fetch(`https://api.shortlovers.id/api/dramas/${dramaId}`, {
            next: { revalidate: 3600 },
        });
        if (!res.ok) return null;
        const data = await res.json();
        return data;
    } catch {
        return null;
    }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const { dramaId } = await params;
    const drama = await getDrama(dramaId);
    return {
        title: drama ? `${drama.title} - KingShort` : 'KingShort - Drama Seru',
        description: drama?.description?.slice(0, 155) || 'Tonton drama pendek seru di KingShort!',
        openGraph: {
            images: drama?.cover ? [drama.cover] : [],
        },
    };
}

export default async function GetDramaPage({ params }: Props) {
    const { dramaId } = await params;
    const drama = await getDrama(dramaId);

    const PLAY_STORE_URL = `https://play.google.com/store/apps/details?id=id.kingshort.mobile&referrer=drama%3D${dramaId}`;
    const DEEP_LINK_URL = `kingshort://drama/${dramaId}`;

    return (
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center px-6 py-12 font-sans">

            {/* Logo */}
            <div className="mb-8 text-center">
                <div className="inline-flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center">
                        <span className="text-black text-sm font-black">K</span>
                    </div>
                    <span className="text-xl font-bold">KingShort</span>
                </div>
                <p className="text-gray-500 text-xs">Drama Pendek, Emosi Panjang</p>
            </div>

            {/* Drama Card */}
            {drama ? (
                <div className="w-full max-w-sm mb-8">
                    <div className="relative rounded-2xl overflow-hidden bg-zinc-900 shadow-2xl">
                        {drama.cover && (
                            <img
                                src={drama.cover}
                                alt={drama.title}
                                className="w-full aspect-[3/4] object-cover"
                            />
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent" />
                        <div className="absolute bottom-0 p-5">
                            <div className="flex flex-wrap gap-1 mb-2">
                                {(drama.genre || []).slice(0, 3).map((g: string) => (
                                    <span key={g} className="text-[10px] bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full border border-yellow-500/30">
                                        {g}
                                    </span>
                                ))}
                            </div>
                            <h1 className="text-xl font-bold leading-snug mb-1">{drama.title}</h1>
                            <p className="text-gray-300 text-sm line-clamp-2">{drama.description}</p>
                            <p className="text-gray-500 text-xs mt-2">{drama.totalEpisodes} Episode</p>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="w-full max-w-sm mb-8 rounded-2xl bg-zinc-900 p-8 text-center">
                    <p className="text-4xl mb-3">🎬</p>
                    <h1 className="text-lg font-bold">Drama Seru Menunggumu!</h1>
                    <p className="text-gray-400 text-sm mt-1">Download KingShort dan mulai nonton sekarang.</p>
                </div>
            )}

            {/* CTA Buttons */}
            <div className="w-full max-w-sm space-y-3">
                {/* Primary: Open in app if installed, else go to Play Store */}
                <a
                    href={DEEP_LINK_URL}
                    className="block w-full py-4 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-full font-bold text-black text-center text-lg shadow-lg hover:brightness-110 transition-all"
                >
                    📱 Buka di Aplikasi
                </a>

                {/* Secondary: Download from Play Store */}
                <a
                    href={PLAY_STORE_URL}
                    className="block w-full py-4 bg-zinc-800 rounded-full font-semibold text-white text-center text-base border border-zinc-700 hover:bg-zinc-700 transition-all"
                >
                    ⬇️ Download KingShort
                </a>
            </div>

            <p className="text-gray-600 text-xs mt-8 text-center">
                Setelah install, drama ini langsung terbuka untukmu 🎉
            </p>
        </div>
    );
}

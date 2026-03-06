"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ChevronLeft, Save, PlayCircle, Trash2, Loader2,
    Image as ImageIcon, Eye, Clock, Film, Globe, Languages,
    ToggleLeft, ToggleRight, ExternalLink, X, Plus, Camera, Link2
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

interface DramaData {
    id: string; title: string; description: string; cover: string;
    banner: string | null; genres: string[]; status: string;
    country: string; language: string; totalEpisodes: number;
    views: number; rating: number; isActive: boolean; isVip: boolean;
    createdAt: string; updatedAt: string;
}

interface Episode {
    id: string; episodeNumber: number; title: string; videoUrl: string;
    thumbnail: string | null; duration: number; views: number;
    isVip: boolean; isActive: boolean;
}

interface Category {
    id: string; name: string; slug: string; icon: string | null;
}

export default function DramaDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const [drama, setDrama] = useState<DramaData | null>(null);
    const [episodes, setEpisodes] = useState<Episode[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [showGenrePicker, setShowGenrePicker] = useState(false);

    // Cover edit state
    const [coverFile, setCoverFile] = useState<File | null>(null);
    const [coverPreview, setCoverPreview] = useState<string | null>(null);
    const [coverUrl, setCoverUrl] = useState("");
    const [showCoverUrlInput, setShowCoverUrlInput] = useState(false);
    const [isUploadingCover, setIsUploadingCover] = useState(false);
    const coverInputRef = useRef<HTMLInputElement>(null);

    const [formData, setFormData] = useState({
        title: "", description: "", status: "", isVip: false, genres: [] as string[]
    });

    useEffect(() => { if (id) fetchData(); }, [id]);

    const fetchData = async () => {
        try {
            const [resDrama, resCats] = await Promise.all([
                fetch(`/api/dramas/${id}`),
                fetch(`/api/categories`),
            ]);
            const dataDrama = await resDrama.json();
            const dataCats = await resCats.json();

            setDrama(dataDrama);
            // Worker API returns episodes embedded in drama response
            const eps = dataDrama.episodes || [];
            setEpisodes(Array.isArray(eps) ? eps : []);
            setCategories(Array.isArray(dataCats) ? dataCats : []);
            setFormData({
                title: dataDrama.title,
                description: dataDrama.description || "",
                status: dataDrama.status,
                isVip: dataDrama.isVip,
                genres: dataDrama.genres || [],
            });
        } catch {
            toast.error("Gagal memuat data");
        } finally {
            setIsLoading(false);
        }
    };

    // Handle cover file selection
    const handleCoverSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            toast.error('File harus berupa gambar');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            toast.error('Ukuran file maksimal 10MB');
            return;
        }
        setCoverFile(file);
        setCoverPreview(URL.createObjectURL(file));
        setCoverUrl("");
        setShowCoverUrlInput(false);
    };

    // Reset cover edit state
    const resetCoverState = () => {
        if (coverPreview) URL.revokeObjectURL(coverPreview);
        setCoverFile(null);
        setCoverPreview(null);
        setCoverUrl("");
        setShowCoverUrlInput(false);
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            let newCoverUrl: string | undefined;

            // Upload cover file if selected
            if (coverFile) {
                setIsUploadingCover(true);
                const uploadData = new FormData();
                uploadData.append('file', coverFile);
                uploadData.append('folder', 'dramas');
                const uploadRes = await fetch('/api/upload', { method: 'POST', body: uploadData });
                if (!uploadRes.ok) throw new Error('Cover upload failed');
                const uploadResult = await uploadRes.json();
                newCoverUrl = uploadResult.url;
                setIsUploadingCover(false);
            } else if (coverUrl.trim()) {
                newCoverUrl = coverUrl.trim();
            }

            const patchBody = {
                ...formData,
                ...(newCoverUrl ? { cover: newCoverUrl } : {}),
            };

            const res = await fetch(`/api/dramas/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(patchBody),
            });
            if (res.ok) {
                toast.success("Perubahan disimpan");
                setIsEditing(false);
                resetCoverState();
                fetchData();
            } else throw new Error("Failed");
        } catch { toast.error("Gagal menyimpan"); }
        finally { setIsSaving(false); setIsUploadingCover(false); }
    };

    const deleteEpisode = async (epId: string) => {
        if (!confirm("Hapus episode ini?")) return;
        try {
            const res = await fetch(`/api/episodes/${epId}`, { method: "DELETE" });
            if (res.ok) { toast.success("Episode dihapus"); fetchData(); }
        } catch { toast.error("Gagal hapus episode"); }
    };

    const addGenre = (genreName: string) => {
        if (!formData.genres.includes(genreName)) {
            setFormData({ ...formData, genres: [...formData.genres, genreName] });
        }
        setShowGenrePicker(false);
    };

    const removeGenre = (genreName: string) => {
        setFormData({ ...formData, genres: formData.genres.filter(g => g !== genreName) });
    };

    // Available genres = categories not yet in formData.genres
    const availableGenres = categories.filter(c => !formData.genres.includes(c.name));

    if (isLoading) return (
        <div className="p-8 space-y-6">
            <Skeleton className="h-8 w-32 bg-zinc-800" />
            <Skeleton className="h-64 w-full rounded-xl bg-zinc-800" />
            <Skeleton className="h-48 w-full rounded-xl bg-zinc-800" />
        </div>
    );

    if (!drama) return (
        <div className="p-8 flex flex-col items-center justify-center text-center gap-4">
            <Film size={48} className="text-zinc-600" />
            <p className="text-zinc-400">Drama not found</p>
            <button onClick={() => router.back()} className="text-cyan-500 hover:text-cyan-400">← Kembali</button>
        </div>
    );

    const sortedEpisodes = [...episodes].sort((a, b) => a.episodeNumber - b.episodeNumber);
    const currentGenres = isEditing ? formData.genres : (drama.genres as string[]);

    return (
        <div className="p-6 lg:p-8 space-y-6 max-w-6xl mx-auto">
            {/* Back + Actions */}
            <div className="flex items-center justify-between">
                <button onClick={() => router.back()} className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
                    <ChevronLeft size={20} />
                    <span className="text-sm font-medium">Kembali</span>
                </button>
                <div className="flex gap-2">
                    {isEditing ? (
                        <>
                            <button onClick={() => { setIsEditing(false); resetCoverState(); fetchData(); }} className="px-4 py-2 text-sm text-zinc-400 border border-zinc-700 rounded-lg hover:bg-zinc-800">
                                Batal
                            </button>
                            <button onClick={handleSave} disabled={isSaving} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-lg font-semibold text-sm">
                                {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                                Simpan
                            </button>
                        </>
                    ) : (
                        <button onClick={() => setIsEditing(true)} className="px-4 py-2 text-sm text-white bg-cyan-600 hover:bg-cyan-700 rounded-lg font-semibold">
                            Edit Drama
                        </button>
                    )}
                </div>
            </div>

            {/* Hero Section */}
            <div className="rounded-xl border border-zinc-800 bg-[#111] overflow-hidden">
                <div className="flex flex-col md:flex-row">
                    {/* Cover */}
                    <div className="md:w-48 lg:w-56 flex-shrink-0 bg-zinc-900 relative group">
                        {/* Hidden file input */}
                        <input
                            ref={coverInputRef}
                            type="file"
                            accept="image/*"
                            className="hidden"
                            onChange={handleCoverSelect}
                        />

                        {/* Cover image or placeholder */}
                        {(coverPreview || drama.cover) ? (
                            <img
                                src={coverPreview || drama.cover}
                                alt={drama.title}
                                className="w-full h-full object-cover aspect-[2/3] md:aspect-auto"
                            />
                        ) : (
                            <div className="aspect-[2/3] flex items-center justify-center text-zinc-600">
                                <ImageIcon size={40} />
                            </div>
                        )}

                        {/* Edit overlay — visible in edit mode */}
                        {isEditing && (
                            <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                onClick={() => coverInputRef.current?.click()}
                            >
                                <Camera size={28} className="text-white" />
                                <span className="text-white text-xs font-semibold">Ganti Cover</span>
                                <button
                                    type="button"
                                    className="mt-1 flex items-center gap-1 text-[10px] text-cyan-400 hover:text-cyan-300 bg-zinc-900/80 px-2 py-1 rounded transition-colors"
                                    onClick={(e) => { e.stopPropagation(); setShowCoverUrlInput(!showCoverUrlInput); }}
                                >
                                    <Link2 size={10} /> Paste URL
                                </button>
                            </div>
                        )}

                        {/* Upload indicator */}
                        {isUploadingCover && (
                            <div className="absolute inset-0 bg-black/70 flex items-center justify-center">
                                <Loader2 className="animate-spin text-cyan-500" size={28} />
                            </div>
                        )}

                        {/* Cover preview badge */}
                        {isEditing && (coverPreview || coverUrl) && (
                            <div className="absolute top-2 right-2 flex gap-1">
                                <span className="bg-emerald-500 text-white text-[10px] px-2 py-0.5 rounded-full font-semibold shadow">Baru</span>
                                <button
                                    onClick={(e) => { e.stopPropagation(); resetCoverState(); }}
                                    className="bg-red-500 hover:bg-red-600 text-white p-0.5 rounded-full shadow transition-colors"
                                >
                                    <X size={12} />
                                </button>
                            </div>
                        )}

                        {/* URL input below cover */}
                        {isEditing && showCoverUrlInput && (
                            <div className="absolute bottom-0 left-0 right-0 bg-zinc-900/95 p-2 border-t border-zinc-700">
                                <input
                                    type="text"
                                    placeholder="https://... cover URL"
                                    className="w-full bg-zinc-800 text-white text-xs px-2 py-1.5 rounded border border-zinc-700 focus:border-cyan-500 focus:outline-none"
                                    value={coverUrl}
                                    onChange={e => { setCoverUrl(e.target.value); setCoverFile(null); setCoverPreview(null); }}
                                />
                            </div>
                        )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 p-6 space-y-4">
                        {/* Title */}
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                                {isEditing ? (
                                    <input
                                        type="text"
                                        className="text-2xl font-bold text-white bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1 w-full focus:outline-none focus:border-cyan-500"
                                        value={formData.title}
                                        onChange={e => setFormData({ ...formData, title: e.target.value })}
                                    />
                                ) : (
                                    <h1 className="text-2xl font-bold text-white">{drama.title}</h1>
                                )}
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                                {drama.isActive ? (
                                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>
                                ) : (
                                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20">Inactive</span>
                                )}
                            </div>
                        </div>

                        {/* Genres — Editable */}
                        <div className="relative">
                            <div className="flex flex-wrap gap-1.5 items-center">
                                {currentGenres?.map(g => (
                                    <span key={g} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                        {g}
                                        {isEditing && (
                                            <button onClick={() => removeGenre(g)} className="hover:text-red-400 transition-colors">
                                                <X size={12} />
                                            </button>
                                        )}
                                    </span>
                                ))}
                                {isEditing && (
                                    <button
                                        onClick={() => setShowGenrePicker(!showGenrePicker)}
                                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-800 text-zinc-400 border border-zinc-700 hover:border-cyan-500 hover:text-cyan-400 transition-colors"
                                    >
                                        <Plus size={12} /> Tambah Genre
                                    </button>
                                )}
                            </div>

                            {/* Genre Picker Dropdown */}
                            {isEditing && showGenrePicker && (
                                <div className="absolute top-full left-0 mt-2 w-72 bg-zinc-900 border border-zinc-700 rounded-xl shadow-xl z-50 max-h-64 overflow-y-auto">
                                    <div className="p-2">
                                        {availableGenres.length > 0 ? (
                                            availableGenres.map(cat => (
                                                <button
                                                    key={cat.id}
                                                    onClick={() => addGenre(cat.name)}
                                                    className="w-full text-left px-3 py-2 rounded-lg text-sm text-zinc-300 hover:bg-cyan-500/10 hover:text-cyan-400 transition-colors flex items-center gap-2"
                                                >
                                                    {cat.icon && <span>{cat.icon}</span>}
                                                    {cat.name}
                                                </button>
                                            ))
                                        ) : (
                                            <div className="px-3 py-4 text-center text-xs text-zinc-500">
                                                <p>Semua genre sudah ditambahkan.</p>
                                                <Link href="/categories" className="text-cyan-400 hover:text-cyan-300 mt-1 inline-block">
                                                    + Buat Genre Baru
                                                </Link>
                                            </div>
                                        )}
                                    </div>
                                    {availableGenres.length > 0 && (
                                        <div className="border-t border-zinc-800 p-2">
                                            <Link href="/categories" className="block text-center text-xs text-zinc-500 hover:text-cyan-400 py-1">
                                                Kelola Genre di Kategori →
                                            </Link>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Meta Info */}
                        <div className="flex flex-wrap gap-4 text-sm text-zinc-400">
                            <span className="flex items-center gap-1.5">
                                <Film size={14} className="text-zinc-500" />
                                <StatusBadge status={isEditing ? formData.status : drama.status} />
                                {isEditing && (
                                    <select
                                        className="bg-zinc-900 border border-zinc-700 rounded px-2 py-0.5 text-xs text-white ml-1"
                                        value={formData.status}
                                        onChange={e => setFormData({ ...formData, status: e.target.value })}
                                    >
                                        <option value="draft">Draft</option>
                                        <option value="ongoing">Ongoing</option>
                                        <option value="completed">Completed</option>
                                    </select>
                                )}
                            </span>
                            <span className="flex items-center gap-1.5">
                                <PlayCircle size={14} className="text-zinc-500" />
                                <span className="text-white font-medium">{drama.totalEpisodes}</span> episode
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Globe size={14} className="text-zinc-500" />
                                {drama.country || 'Unknown'}
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Languages size={14} className="text-zinc-500" />
                                {drama.language || 'Unknown'}
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Eye size={14} className="text-zinc-500" />
                                {(drama.views ?? 0).toLocaleString()} views
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Clock size={14} className="text-zinc-500" />
                                {new Date(drama.createdAt).toLocaleDateString('id-ID', { year: 'numeric', month: 'long', day: 'numeric' })}
                            </span>
                        </div>

                        {/* VIP */}
                        {isEditing ? (
                            <button
                                onClick={() => setFormData({ ...formData, isVip: !formData.isVip })}
                                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-colors ${formData.isVip ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-zinc-800 text-zinc-400 border-zinc-700'}`}
                            >
                                {formData.isVip ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
                                {formData.isVip ? 'VIP' : 'Free'}
                            </button>
                        ) : drama.isVip && (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                ⭐ VIP Exclusive
                            </span>
                        )}

                        {/* Description */}
                        <div>
                            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-1">Deskripsi</h3>
                            {isEditing ? (
                                <textarea
                                    rows={3}
                                    className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:border-cyan-500"
                                    value={formData.description}
                                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                                />
                            ) : (
                                <p className="text-sm text-zinc-300 leading-relaxed">
                                    {drama.description || <span className="text-zinc-600 italic">Tidak ada deskripsi.</span>}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Episode List */}
            <div className="rounded-xl border border-zinc-800 bg-[#111]">
                <div className="flex items-center justify-between p-5 border-b border-zinc-800">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <PlayCircle size={20} className="text-cyan-500" />
                        Episode ({episodes.length}{drama.totalEpisodes > 0 && episodes.length !== drama.totalEpisodes ? ` / ${drama.totalEpisodes}` : ''})
                    </h3>
                    {drama.totalEpisodes > 0 && episodes.length < drama.totalEpisodes && (
                        <span className="text-xs px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                            {drama.totalEpisodes - episodes.length} episode belum terdaftar
                        </span>
                    )}
                </div>

                <div className="p-4">
                    {sortedEpisodes.length > 0 ? (
                        <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-2">
                            {sortedEpisodes.map(ep => (
                                <div
                                    key={ep.id}
                                    onClick={() => ep.videoUrl && window.open(ep.videoUrl, '_blank')}
                                    className={`group relative aspect-[2/1] rounded-lg border border-emerald-500/40 bg-[#1a1a1a] flex items-center justify-center transition-all ${ep.videoUrl ? 'cursor-pointer hover:border-emerald-400 hover:bg-emerald-500/5' : 'cursor-default opacity-60'}`}
                                >
                                    <span className="text-emerald-400 font-bold text-sm">{ep.episodeNumber}</span>

                                    {/* Hover tooltip */}
                                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 w-48">
                                        <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-3 shadow-xl text-xs">
                                            <p className="text-white font-semibold truncate">{ep.title || `Episode ${ep.episodeNumber}`}</p>
                                            <div className="flex items-center gap-3 text-zinc-400 mt-1.5">
                                                <span className="flex items-center gap-1"><Eye size={10} /> {ep.views}</span>
                                                {ep.duration > 0 && (
                                                    <span className="flex items-center gap-1">
                                                        <Clock size={10} /> {Math.floor(ep.duration / 60)}:{String(ep.duration % 60).padStart(2, '0')}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2 mt-2">
                                                {ep.isVip && <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px]">VIP</span>}
                                                <button onClick={(e) => { e.stopPropagation(); deleteEpisode(ep.id); }}
                                                    className="text-red-400 hover:text-red-300 flex items-center gap-0.5 ml-auto">
                                                    <Trash2 size={10} /> Hapus
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="p-8 text-center text-zinc-500">
                            <PlayCircle className="mx-auto mb-2 text-zinc-600" size={32} />
                            <p>Belum ada episode.</p>
                        </div>
                    )}
                </div>
            </div>

            <p className="text-xs text-zinc-600 text-center py-2">
                Drama ID: <code className="text-zinc-500">{drama.id}</code>
            </p>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const styles: Record<string, string> = {
        completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
        ongoing: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
        draft: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
    };
    return (
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${styles[status] || styles.draft}`}>
            {status}
        </span>
    );
}

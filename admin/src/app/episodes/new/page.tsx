"use client";

import { useState, useEffect, Suspense } from "react";
import { Upload, Image as ImageIcon, ChevronRight, Save, CheckCircle2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";

// Type definitions
interface Drama {
    id: string;
    title: string;
    cover: string;
    status: string;
}

function NewEpisodeForm() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [dragActive, setDragActive] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Data Loading
    const [dramas, setDramas] = useState<Drama[]>([]);

    // Form Selection
    const [selectedDramaId, setSelectedDramaId] = useState("");
    const [selectedDrama, setSelectedDrama] = useState<Drama | null>(null);

    // Form Inputs
    const [episodeNumber, setEpisodeNumber] = useState("1");
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [isVip, setIsVip] = useState(false);

    // Files
    const [videoFile, setVideoFile] = useState<File | null>(null);
    const [thumbnailFile, setThumbnailFile] = useState<File | null>(null);
    const [thumbnailPreview, setThumbnailPreview] = useState("");

    // Load available dramas
    useEffect(() => {
        const fetchDramas = async () => {
            try {
                const res = await fetch('/api/dramas?limit=100');
                const data = await res.json();
                setDramas(data.dramas);

                // Check URL params after loading
                const idParam = searchParams.get("dramaId");
                if (idParam && data.dramas) {
                    const found = data.dramas.find((d: Drama) => d.id === idParam);
                    if (found) {
                        setSelectedDramaId(found.id);
                        setSelectedDrama(found);
                    }
                }
            } catch (err) {
                console.error("Failed to load dramas", err);
            }
        };
        fetchDramas();
    }, [searchParams]);

    const handleDramaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const id = e.target.value;
        setSelectedDramaId(id);
        const drama = dramas.find(d => d.id === id);
        setSelectedDrama(drama || null);
    };

    const handleVideoFile = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setVideoFile(e.target.files[0]);
        }
    };

    const handleThumbnailFile = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setThumbnailFile(e.target.files[0]);
            setThumbnailPreview(URL.createObjectURL(e.target.files[0]));
        }
    };

    const handleSubmit = async () => {
        if (!selectedDramaId || !title || !videoFile) {
            toast.error("Wajib isi: Drama, Judul, dan File Video");
            return;
        }

        setIsLoading(true);

        try {
            // 1. Upload Video
            const videoFormData = new FormData();
            videoFormData.append("file", videoFile);
            videoFormData.append("folder", "episodes/videos");
            const vidRes = await fetch("/api/upload", { method: "POST", body: videoFormData });
            if (!vidRes.ok) throw new Error("Video upload failed");
            const vidData = await vidRes.json();
            const videoUrl = vidData.url;

            // 2. Upload Thumbnail (Optional)
            let thumbnailUrl = "";
            if (thumbnailFile) {
                const thumbFormData = new FormData();
                thumbFormData.append("file", thumbnailFile);
                thumbFormData.append("folder", "episodes/thumbnails");
                const thumbRes = await fetch("/api/upload", { method: "POST", body: thumbFormData });
                if (thumbRes.ok) {
                    const thumbData = await thumbRes.json();
                    thumbnailUrl = thumbData.url;
                }
            }

            // 3. Create Episode Record
            const episodeData = {
                episodeNumber: parseInt(episodeNumber),
                title,
                description,
                videoUrl,
                thumbnail: thumbnailUrl,
                isVip,
                duration: 60, // Mock duration or extract from file if possible
            };

            const res = await fetch(`/api/dramas/${selectedDramaId}/episodes`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(episodeData)
            });

            if (!res.ok) throw new Error("Failed to save episode data");

            toast.success("Episode Berhasil Diunggah!", {
                description: `Episode ${episodeNumber} untuk ${selectedDrama?.title} telah tersimpan.`
            });

            router.push(`/dramas/${selectedDramaId}`); // Redirect to drama detail

        } catch (error: any) {
            toast.error("Gagal Mengunggah", { description: error.message });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            {/* Header omitted for brevity, keeping same style */}
            <div className="flex items-center gap-2 text-sm text-zinc-500 mb-6">
                <Link href="/" className="hover:text-zinc-300">Home</Link>
                <ChevronRight size={14} />
                <Link href="/episodes" className="hover:text-zinc-300">Episode</Link>
                <ChevronRight size={14} />
                <span className="text-white">Unggah Episode</span>
            </div>

            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Unggah Video Baru</h1>
                    <p className="text-zinc-400 mt-1">Tambahkan episode baru ke database drama</p>
                </div>
                <div className="flex gap-3">
                    <button onClick={() => router.back()} className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors font-medium">
                        Batal
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className="px-6 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors font-bold flex items-center gap-2 disabled:opacity-50"
                    >
                        {isLoading ? <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Upload size={18} />}
                        Unggah Episode
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* LEFT: Uploads */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Target Drama Card */}
                    {selectedDrama ? (
                        <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 flex items-center gap-4">
                            {/* Assuming cover is URL, if generic class used before, now using img tag */}
                            <img src={selectedDrama.cover || "/placeholder.jpg"} className="h-16 w-12 rounded object-cover flex-shrink-0 bg-zinc-800" />
                            <div>
                                <p className="text-blue-400 text-xs font-bold uppercase tracking-wide">Target Drama</p>
                                <h3 className="text-white font-bold text-lg">{selectedDrama.title}</h3>
                            </div>
                            <div className="ml-auto"><CheckCircle2 className="text-blue-500" size={24} /></div>
                        </div>
                    ) : (
                        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 flex items-center gap-4">
                            <AlertCircle className="text-yellow-500" size={24} />
                            <div>
                                <h3 className="text-yellow-500 font-bold">Belum Ada Drama Dipilih</h3>
                                <p className="text-zinc-400 text-sm">Pilih drama di panel kanan.</p>
                            </div>
                        </div>
                    )}

                    {/* Video Upload */}
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-white">File Video</h3>
                            <span className="text-xs bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded border border-blue-500/20">Wajib</span>
                        </div>
                        <label className={`border-2 border-dashed rounded-xl h-48 flex flex-col items-center justify-center transition-colors cursor-pointer ${videoFile ? 'border-purple-500 bg-purple-500/5' : 'border-zinc-700 hover:border-zinc-600'}`}>
                            <input type="file" accept="video/*" className="hidden" onChange={handleVideoFile} />
                            {videoFile ? (
                                <div className="text-center">
                                    <CheckCircle2 size={40} className="text-purple-500 mx-auto mb-2" />
                                    <p className="text-white font-medium">{videoFile.name}</p>
                                    <p className="text-xs text-zinc-500">{(videoFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                                </div>
                            ) : (
                                <>
                                    <Upload size={32} className="text-zinc-400 mb-2" />
                                    <h4 className="text-white font-medium">Klik untuk Upload Video</h4>
                                </>
                            )}
                        </label>
                    </div>

                    {/* Thumbnail Upload */}
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                        <h3 className="font-semibold text-white mb-4">Thumbnail</h3>
                        <label className="flex gap-6 cursor-pointer group">
                            <input type="file" accept="image/*" className="hidden" onChange={handleThumbnailFile} />
                            <div className="w-48 h-28 bg-zinc-900 rounded-lg border border-zinc-700 flex items-center justify-center flex-shrink-0 overflow-hidden relative">
                                {thumbnailPreview ? (
                                    <img src={thumbnailPreview} className="w-full h-full object-cover" />
                                ) : (
                                    <ImageIcon size={32} className="text-zinc-700 group-hover:text-zinc-500" />
                                )}
                            </div>
                            <div className="flex-1">
                                <p className="text-sm text-zinc-400">Klik untuk unggah cover episode.</p>
                                <div className="mt-2 px-4 py-2 bg-zinc-800 text-white rounded-lg text-sm inline-block">Pilih Gambar</div>
                            </div>
                        </label>
                    </div>
                </div>

                {/* RIGHT: Details */}
                <div className="space-y-6">
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-white mb-4">Detail Episode</h3>

                        <div className="space-y-1.5">
                            <label className="text-sm text-zinc-400">Pilih Drama</label>
                            <select
                                value={selectedDramaId}
                                onChange={handleDramaChange}
                                className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
                            >
                                <option value="">Pilih judul drama...</option>
                                {dramas.map(d => (
                                    <option key={d.id} value={d.id}>{d.title}</option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <label className="text-sm text-zinc-400">No. Episode</label>
                                <input
                                    type="number"
                                    value={episodeNumber}
                                    onChange={(e) => setEpisodeNumber(e.target.value)}
                                    className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
                                />
                            </div>
                            <div className="space-y-1.5 pt-7">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={isVip}
                                        onChange={(e) => setIsVip(e.target.checked)}
                                        className="h-4 w-4 rounded border-zinc-700 bg-black text-purple-600 focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-white font-medium">VIP Only?</span>
                                </label>
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm text-zinc-400">Judul Episode</label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
                                placeholder="Contoh: Pertemuan Pertama"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm text-zinc-400">Sinopsis</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500 h-24 resize-none"
                            />
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}

export default function NewEpisodePage() {
    return (
        <Suspense fallback={<div className="p-8 text-white">Loading...</div>}>
            <NewEpisodeForm />
        </Suspense>
    );
}

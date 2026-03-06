"use client";

import { useState } from "react";
import { Upload, Image as ImageIcon, ChevronRight, Save, Plus, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function NewDramaPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    // Form Data
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [status, setStatus] = useState("ongoing");
    const [tags, setTags] = useState<string[]>([]);
    const [newTag, setNewTag] = useState("trending");

    // Genres
    const [genres, setGenres] = useState(["Romance"]);
    const [newGenre, setNewGenre] = useState("");

    // Cover Image
    const [coverFile, setCoverFile] = useState<File | null>(null);
    const [coverPreview, setCoverPreview] = useState<string>("");

    const addGenre = () => {
        if (newGenre && !genres.includes(newGenre)) {
            setGenres([...genres, newGenre]);
            setNewGenre("");
        }
    };

    const removeGenre = (genre: string) => {
        setGenres(genres.filter(g => g !== genre));
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setCoverFile(file);
            setCoverPreview(URL.createObjectURL(file));
        }
    };

    const handleSubmit = async () => {
        if (!title || !description || !coverFile) {
            toast.error("Please fill in all required fields (Title, Description, Cover)");
            return;
        }

        setIsLoading(true);

        try {
            // 1. Upload Cover
            const formData = new FormData();
            formData.append("file", coverFile);
            formData.append("folder", "dramas");

            const uploadRes = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });

            if (!uploadRes.ok) throw new Error("Failed to upload cover image");
            const uploadData = await uploadRes.json();
            const coverUrl = uploadData.url;

            // 2. Create Drama
            const dramaData = {
                title,
                description,
                status,
                genres,
                tags: tags.length ? tags : [newTag], // Basic tag logic
                cover: coverUrl,
                isFeatured: newTag === "trending" || newTag === "hot",
            };

            const res = await fetch("/api/dramas", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dramaData)
            });

            if (!res.ok) throw new Error("Failed to create drama");

            toast.success("Drama Created Successfully!", {
                description: `${title} has been added to the library.`
            });

            router.push("/dramas");

        } catch (error: any) {
            toast.error("Error creating drama", { description: error.message });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            {/* Breadcrumbs */}
            <div className="flex items-center gap-2 text-sm text-zinc-500 mb-6">
                <Link href="/" className="hover:text-zinc-300">Home</Link>
                <ChevronRight size={14} />
                <Link href="/dramas" className="hover:text-zinc-300">Manajemen Drama</Link>
                <ChevronRight size={14} />
                <span className="text-white">Tambah Drama Baru</span>
            </div>

            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Buat Drama Baru</h1>
                    <p className="text-zinc-400 mt-1">Isi informasi detail untuk membuat judul drama baru.</p>
                </div>
                <div className="flex gap-3">
                    <button onClick={() => router.back()} className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white transition-colors font-medium">
                        Batal
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className="px-6 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors font-bold flex items-center gap-2 disabled:opacity-50"
                    >
                        {isLoading ? <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save size={18} />}
                        Simpan Drama
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* LEFT COLUMN - Cover Image */}
                <div className="space-y-6">
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6">
                        <h3 className="font-semibold text-white mb-4">Cover / Poster Drama</h3>

                        <label className="cursor-pointer group">
                            <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
                            <div className={`aspect-[2/3] bg-zinc-900 rounded-lg border-2 border-dashed ${coverPreview ? 'border-purple-500' : 'border-zinc-700 hover:border-zinc-600'} flex flex-col items-center justify-center transition-colors relative overflow-hidden`}>
                                {coverPreview ? (
                                    <img src={coverPreview} alt="Preview" className="w-full h-full object-cover" />
                                ) : (
                                    <>
                                        <div className="h-16 w-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4 group-hover:bg-zinc-700 transition-colors">
                                            <ImageIcon size={32} className="text-zinc-400 group-hover:text-white" />
                                        </div>
                                        <p className="text-sm font-medium text-white mb-1">Upload Poster</p>
                                        <p className="text-xs text-zinc-500">Rasio 2:3 (Vertical)</p>
                                    </>
                                )}
                            </div>
                        </label>
                        <p className="text-xs text-zinc-500 mt-4 text-center">
                            Disarankan ukuran 1080x1620px. Maks 5MB. Format JPG/PNG.
                        </p>
                    </div>
                </div>

                {/* RIGHT COLUMN - Drama Details */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 space-y-6">
                        <h3 className="font-semibold text-white mb-4">Informasi Utama</h3>

                        <div className="space-y-1.5">
                            <label className="text-sm text-zinc-400">Judul Drama</label>
                            <input
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                type="text"
                                className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
                                placeholder="Contoh: Cinta di Musim Hujan"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-sm text-zinc-400">Sinopsis Lengkap</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500 h-32 resize-none"
                                placeholder="Ceritakan gambaran besar tentang drama ini..."
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            <div className="space-y-1.5">
                                <label className="text-sm text-zinc-400">Status Awal</label>
                                <select
                                    value={status}
                                    onChange={(e) => setStatus(e.target.value)}
                                    className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
                                >
                                    <option value="draft">Draft (Disembunyikan)</option>
                                    <option value="ongoing">Ongoing (Tayang)</option>
                                    <option value="completed">Completed (Tamat)</option>
                                </select>
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-sm text-zinc-400">Label Khusus</label>
                                <select
                                    value={newTag}
                                    onChange={(e) => setNewTag(e.target.value)}
                                    className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500"
                                >
                                    <option value="none">Tidak Ada</option>
                                    <option value="trending">Trending</option>
                                    <option value="hot">Hot New</option>
                                    <option value="exclusive">Exclusive</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <label className="text-sm text-zinc-400">Genre & Kategori</label>
                            <div className="flex flex-wrap gap-2 mb-2">
                                {genres.map(g => (
                                    <span key={g} className="bg-purple-500/20 text-purple-400 border border-purple-500/30 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                                        {g}
                                        <button onClick={() => removeGenre(g)} className="hover:text-white"><X size={14} /></button>
                                    </span>
                                ))}
                            </div>
                            <div className="flex gap-2">
                                <select
                                    className="bg-black/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-purple-500 flex-1"
                                    value={newGenre}
                                    onChange={(e) => setNewGenre(e.target.value)}
                                >
                                    <option value="">Pilih Genre...</option>
                                    <option value="Action">Action</option>
                                    <option value="Comedy">Comedy</option>
                                    <option value="Drama">Drama</option>
                                    <option value="Fantasy">Fantasy</option>
                                    <option value="Horror">Horror</option>
                                    <option value="Romance">Romance</option>
                                    <option value="Thriller">Thriller</option>
                                </select>
                                <button
                                    type="button"
                                    onClick={addGenre}
                                    className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 rounded-lg transition-colors"
                                >
                                    <Plus size={20} />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}

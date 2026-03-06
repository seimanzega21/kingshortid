"use client";

import { useState, useEffect } from "react";
import {
    Search,
    Plus,
    Edit,
    Trash2,
    Tags,
    X,
    Loader2
} from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

interface Category {
    id: string;
    name: string;
    slug: string;
    icon?: string;
    order: number;
    count?: number; // Optional, might need aggregate query later
}

export default function CategoriesPage() {
    const [categories, setCategories] = useState<Category[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isInternalLoading, setIsInternalLoading] = useState(false);
    const [showModal, setShowModal] = useState(false);

    // Form State
    const [name, setName] = useState("");
    const [slug, setSlug] = useState("");
    const [order, setOrder] = useState(0);

    const fetchCategories = async () => {
        try {
            const res = await fetch("/api/categories");
            const data = await res.json();
            setCategories(data);
        } catch (error) {
            toast.error("Failed to load categories");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCategories();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsInternalLoading(true);
        try {
            const res = await fetch("/api/categories", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, slug, order })
            });

            if (res.ok) {
                toast.success("Category Created");
                fetchCategories();
                setShowModal(false);
                setName("");
                setSlug("");
                setOrder(0);
            } else {
                throw new Error("Failed");
            }
        } catch (error) {
            toast.error("Failed to create category");
        } finally {
            setIsInternalLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure?")) return;
        try {
            const res = await fetch(`/api/categories/${id}`, { method: "DELETE" });
            if (res.ok) {
                toast.success("Category Deleted");
                fetchCategories();
            }
        } catch (error) {
            toast.error("Failed to delete");
        }
    };

    return (
        <div className="p-8 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Genre & Kategori</h1>
                    <p className="text-zinc-400 mt-1">Atur kategori dan tag untuk memudahkan pencarian drama.</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors">
                    <Plus size={18} />
                    <span>Tambah Kategori</span>
                </button>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Category List */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="rounded-xl border border-zinc-800 bg-[#121212] overflow-hidden">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-[#1A1A1A] border-b border-zinc-800 text-xs uppercase text-zinc-500">
                                <tr>
                                    <th className="px-6 py-4 font-semibold">Nama Kategori</th>
                                    <th className="px-6 py-4 font-semibold">Slug</th>
                                    <th className="px-6 py-4 font-semibold">Order</th>
                                    <th className="px-6 py-4 text-right">Aksi</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-800">
                                {isLoading ? (
                                    Array(5).fill(0).map((_, i) => (
                                        <tr key={i}>
                                            <td className="px-6 py-4"><Skeleton className="h-6 w-32" /></td>
                                            <td className="px-6 py-4"><Skeleton className="h-6 w-20" /></td>
                                            <td className="px-6 py-4"><Skeleton className="h-6 w-10" /></td>
                                            <td className="px-6 py-4"><Skeleton className="h-8 w-8 ml-auto" /></td>
                                        </tr>
                                    ))
                                ) : categories.length > 0 ? (
                                    categories.map((item) => (
                                        <tr key={item.id} className="group hover:bg-zinc-800/50 transition-colors">
                                            <td className="px-6 py-4 font-medium text-white flex items-center gap-2">
                                                <Tags size={14} className="text-zinc-500" />
                                                {item.name}
                                            </td>
                                            <td className="px-6 py-4 text-zinc-500">{item.slug}</td>
                                            <td className="px-6 py-4 text-zinc-500">{item.order}</td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex justify-end gap-2">
                                                    <button
                                                        onClick={() => handleDelete(item.id)}
                                                        className="p-1.5 hover:bg-zinc-700 rounded text-zinc-400 hover:text-red-500 transition-colors">
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-8 text-center text-zinc-500">
                                            Belum ada kategori.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Quick Add / Info Side */}
                <div className="space-y-6">
                    <div className="rounded-xl border border-zinc-800 bg-[#121212] p-6">
                        <h3 className="font-semibold text-white mb-4">Statistik Genre</h3>
                        <div className="space-y-4">
                            {[
                                { label: "Total Kategori", value: categories.length.toString() },
                            ].map((stat, i) => (
                                <div key={i} className="flex justify-between items-center py-2 border-b border-zinc-800 last:border-0">
                                    <span className="text-sm text-zinc-400">{stat.label}</span>
                                    <span className="text-sm font-medium text-white">{stat.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
                    <div className="bg-[#121212] border border-zinc-800 rounded-xl p-6 w-full max-w-md space-y-6">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-bold text-white">Tambah Kategori</h3>
                            <button onClick={() => setShowModal(false)}><X className="text-zinc-400" /></button>
                        </div>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm text-zinc-400">Nama Kategori</label>
                                <input
                                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-white"
                                    value={name}
                                    onChange={e => setName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-zinc-400">slug (Optional)</label>
                                <input
                                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-white"
                                    value={slug}
                                    onChange={e => setSlug(e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm text-zinc-400">Order Priority</label>
                                <input
                                    type="number"
                                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-white"
                                    value={order}
                                    onChange={e => setOrder(parseInt(e.target.value))}
                                />
                            </div>
                            <button
                                disabled={isInternalLoading}
                                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 rounded-lg flex justify-center">
                                {isInternalLoading ? <Loader2 className="animate-spin" /> : "Simpan"}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

"use client";

import { MobileLayout } from "@/components/MobileLayout";
import { useState } from "react";
import { clsx } from "clsx";
import { Play, Trash2 } from "lucide-react";

export default function LibraryPage() {
    const [activeTab, setActiveTab] = useState<"history" | "watchlist">("history");

    const historyItems = [1, 2, 3, 4];
    const watchlistItems = [5, 6];

    const items = activeTab === "history" ? historyItems : watchlistItems;

    return (
        <MobileLayout>
            <div className="min-h-screen bg-black text-white pb-24">

                {/* Header */}
                <div className="pt-8 px-4 pb-4 bg-black sticky top-0 z-10 border-b border-zinc-900">
                    <h1 className="text-xl font-bold mb-4">Library</h1>

                    {/* Tabs */}
                    <div className="flex p-1 bg-zinc-900 rounded-lg">
                        {(["history", "watchlist"] as const).map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={clsx(
                                    "flex-1 py-2 text-sm font-medium rounded-md capitalize transition-all",
                                    activeTab === tab
                                        ? "bg-zinc-800 text-white shadow"
                                        : "text-gray-500 hover:text-gray-300"
                                )}
                            >
                                {tab === "history" ? "Riwayat" : "Koleksi Saya"}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content Grid */}
                <div className="p-4 grid grid-cols-3 gap-3">
                    {items.map((id) => (
                        <div key={id} className="group relative aspect-[3/4] bg-zinc-800 rounded-lg overflow-hidden border border-zinc-800">
                            {/* Cover Placeholder */}
                            <div className="absolute inset-0 bg-zinc-800 animate-pulse" />

                            {/* Item Info overlay */}
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end p-2">
                                <h4 className="text-xs font-bold leading-tight mb-1">Drama Title {id}</h4>
                                {activeTab === "history" && (
                                    <div className="w-full bg-zinc-700 h-1 rounded-full overflow-hidden">
                                        <div className="bg-yellow-500 h-full w-[60%]" />
                                    </div>
                                )}
                            </div>

                            {/* Play Button Overlay */}
                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
                                <Play className="fill-white text-white w-8 h-8" />
                            </div>
                        </div>
                    ))}
                </div>

                {/* Empty State */}
                {items.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-gray-500 space-y-4">
                        <div className="w-16 h-16 bg-zinc-900 rounded-full flex items-center justify-center">
                            <Play className="opacity-50" />
                        </div>
                        <p>Belum ada {activeTab === "history" ? "riwayat" : "koleksi"}.</p>
                    </div>
                )}

            </div>
        </MobileLayout>
    );
}

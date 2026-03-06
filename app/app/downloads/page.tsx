"use client";

import { MobileLayout } from "@/components/MobileLayout";
import { ChevronLeft, Download, Trash2, Play } from "lucide-react";
import Link from "next/link";

export default function DownloadsPage() {
    const downloads = [
        { id: 1, title: "The CEO's Secret Wife", episodes: "Ep. 1-10", size: "250MB", progress: 100 },
        { id: 2, title: "Love in the Palace", episodes: "Ep. 1-5", size: "120MB", progress: 65 },
    ];

    return (
        <MobileLayout showNav={false}>
            <div className="min-h-screen bg-black text-white p-6">

                {/* Header */}
                <div className="flex items-center gap-4 mb-4">
                    <Link href="/profile" className="p-2 -ml-2 text-gray-400 hover:text-white bg-zinc-900 rounded-full">
                        <ChevronLeft size={24} />
                    </Link>
                    <h1 className="text-xl font-bold">Unduhan</h1>
                    <div className="ml-auto flex flex-col items-end">
                        <span className="text-[10px] text-gray-400 uppercase font-bold">Storage</span>
                        <div className="bg-zinc-800 h-1.5 w-20 rounded-full mt-1 overflow-hidden">
                            <div className="bg-green-500 w-[65%] h-full" />
                        </div>
                        <span className="text-[10px] text-gray-500 mt-1">12 GB Free</span>
                    </div>
                </div>

                {/* List */}
                <div className="space-y-4 mt-6">
                    {downloads.map((item) => (
                        <div key={item.id} className="bg-zinc-900/50 rounded-2xl p-4 border border-zinc-900 flex gap-4">

                            {/* Cover */}
                            <div className="w-16 h-24 bg-zinc-800 rounded-lg shrink-0 overflow-hidden relative">
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <Play className="fill-white text-white w-6 h-6 opacity-80" />
                                </div>
                            </div>

                            <div className="flex-1 flex flex-col justify-between py-1">
                                <div>
                                    <h3 className="font-bold text-sm leading-tight mb-1">{item.title}</h3>
                                    <p className="text-xs text-gray-400">{item.episodes} • {item.size}</p>
                                </div>

                                <div>
                                    {item.progress < 100 ? (
                                        <div className="space-y-1">
                                            <div className="flex justify-between text-[10px] text-yellow-500 font-bold">
                                                <span>Downloading...</span>
                                                <span>{item.progress}%</span>
                                            </div>
                                            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                                <div className="h-full bg-yellow-500" style={{ width: `${item.progress}%` }} />
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-3">
                                            <button className="flex-1 bg-white text-black text-xs font-bold py-1.5 rounded-full">
                                                Play Offline
                                            </button>
                                            <button className="p-1.5 text-red-500 bg-zinc-800 rounded-full">
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {downloads.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-32 opacity-50">
                        <Download size={48} className="mb-4" />
                        <p>No downloads yet</p>
                    </div>
                )}

            </div>
        </MobileLayout>
    );
}

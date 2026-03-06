"use client";

import { X, Lock, Play } from "lucide-react";
import { clsx } from "clsx";
import Image from "next/image";

interface EpisodeSheetProps {
    isOpen: boolean;
    onClose: () => void;
}

export function EpisodeSheet({ isOpen, onClose }: EpisodeSheetProps) {
    // Mock data for episodes
    const episodes = Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        title: `Episode ${i + 1}`,
        isLocked: i > 4, // Lock episodes after 5
        isCurrent: i === 0,
        duration: "1:30"
    }));

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Sheet Content */}
            <div className="relative w-full max-w-md bg-zinc-900 rounded-t-3xl sm:rounded-3xl max-h-[85vh] flex flex-col shadow-2xl animate-in slide-in-from-bottom duration-300">

                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-zinc-800">
                    <div>
                        <h3 className="text-lg font-bold text-white">Episodes</h3>
                        <p className="text-xs text-gray-400">Update to Ep. 80</p>
                    </div>
                    <button onClick={onClose} className="p-2 text-gray-400 hover:text-white bg-zinc-800 rounded-full">
                        <X size={20} />
                    </button>
                </div>

                {/* Drama Info Summary */}
                <div className="p-4 flex gap-4 bg-zinc-800/50">
                    <div className="w-16 h-24 bg-zinc-700 rounded-lg shrink-0 overflow-hidden relative">
                        {/* Cover Placeholder */}
                        <div className="absolute inset-0 bg-gradient-to-tr from-yellow-600 to-black" />
                    </div>
                    <div className="flex-1 space-y-2">
                        <h4 className="font-bold text-white line-clamp-1">The CEO's Secret Wife</h4>
                        <p className="text-xs text-gray-400 line-clamp-2">
                            A thrilling romance about hidden identities and a contract marriage...
                        </p>
                        <div className="flex gap-2">
                            <span className="text-[10px] bg-yellow-500/20 text-yellow-500 px-2 py-0.5 rounded border border-yellow-500/30">Romance</span>
                            <span className="text-[10px] bg-zinc-700 text-gray-300 px-2 py-0.5 rounded">Ongoing</span>
                        </div>
                    </div>
                </div>

                {/* Episode List Grid */}
                <div className="flex-1 overflow-y-auto p-4">
                    <div className="grid grid-cols-5 gap-3">
                        {episodes.map((ep) => (
                            <button
                                key={ep.id}
                                className={clsx(
                                    "aspect-square rounded-xl flex flex-col items-center justify-center relative border transition-all",
                                    ep.isCurrent
                                        ? "bg-yellow-500 border-yellow-500 text-black font-bold shadow-[0_0_15px_rgba(255,215,0,0.4)]"
                                        : "bg-zinc-800 border-zinc-700 text-gray-300 hover:bg-zinc-700"
                                )}
                            >
                                <span className="text-lg">{ep.id}</span>
                                {ep.isLocked && (
                                    <div className="absolute -top-1 -right-1">
                                        <div className="bg-black/50 rounded-full p-0.5 border border-zinc-600">
                                            <Lock size={10} className="text-yellow-500" />
                                        </div>
                                    </div>
                                )}
                                {ep.isCurrent && (
                                    <div className="absolute -bottom-1">
                                        <Play size={8} className="fill-black text-black" />
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="p-4 border-t border-zinc-800 bg-zinc-900 pb-safe-area-bottom">
                    <button className="w-full py-3 bg-gradient-to-r from-yellow-500 to-yellow-600 text-black font-bold rounded-full shadow-lg shadow-yellow-500/20">
                        Unlock All Episodes
                    </button>
                </div>

            </div>
        </div>
    );
}

"use client";

import { MobileLayout } from "@/components/MobileLayout";
import { Search, Play, Star, ChevronRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { clsx } from "clsx";

export default function DiscoverPage() {
    const categories = ["All", "Romance", "Thriller", "CEO", "Revenge", "Fantasy"];

    const trending = [1, 2, 3, 4, 5]; // IDs

    return (
        <MobileLayout>
            <div className="pb-24 px-4 pt-6 space-y-8 bg-black min-h-screen text-white">

                {/* Search Bar */}
                <div className="relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                        <Search size={20} />
                    </div>
                    <input
                        type="text"
                        placeholder="Search titles, actors, genres..."
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-full py-3 pl-12 pr-4 text-sm text-white focus:outline-none focus:border-yellow-500/50 transition-all placeholder:text-zinc-500"
                    />
                </div>

                {/* Categories */}
                <div className="flex space-x-3 overflow-x-auto scrollbar-hide pb-2 -mx-4 px-4">
                    {categories.map((cat, i) => (
                        <button
                            key={cat}
                            className={clsx(
                                "px-5 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all",
                                i === 0
                                    ? "bg-gradient-to-r from-yellow-500 to-yellow-600 text-black shadow-lg shadow-yellow-500/20"
                                    : "bg-zinc-900 text-gray-300 border border-zinc-800"
                            )}
                        >
                            {cat}
                        </button>
                    ))}
                </div>

                {/* Hero Section (For You) */}
                <section>
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold">For You</h2>
                    </div>
                    <div className="relative w-full aspect-[16/9] rounded-2xl overflow-hidden shadow-2xl shadow-yellow-900/10 border border-zinc-800 group">
                        {/* Background Image Placeholder */}
                        <div className="absolute inset-0 bg-zinc-800" />
                        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?q=80&w=2070&auto=format&fit=crop')] bg-cover bg-center" />

                        {/* Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />

                        {/* Content */}
                        <div className="absolute bottom-4 left-4 right-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
                            <div className="flex gap-2 mb-2">
                                <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-500 text-[10px] font-bold rounded uppercase border border-yellow-500/30 backdrop-blur-sm">New</span>
                                <span className="text-xs text-gray-300 font-medium backdrop-blur-sm bg-black/30 px-2 rounded">Romance • 80 Eps</span>
                            </div>
                            <h3 className="text-2xl font-bold mb-2 leading-tight">The CEO's Secret Wife</h3>
                            <p className="text-gray-300 text-xs line-clamp-2 mb-4 max-w-[90%]">
                                After a contract marriage, she discovers her husband is the heir to a global empire...
                            </p>
                            <div className="flex gap-3">
                                <button className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-full font-bold text-black text-sm hover:brightness-110">
                                    <Play className="fill-black w-4 h-4" />
                                    Watch Now
                                </button>
                                <button className="px-3 bg-zinc-800/80 backdrop-blur rounded-full text-white border border-white/10">
                                    <Star className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Trending Now */}
                <section>
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-xl font-bold">Trending Now</h2>
                        <Link href="#" className="text-xs text-yellow-500 font-medium hover:underline">See all</Link>
                    </div>
                    <div className="flex space-x-4 overflow-x-auto scrollbar-hide -mx-4 px-4 pb-4">
                        {trending.map((id, index) => (
                            <div key={id} className="relative flex-none w-[140px] group cursor-pointer">
                                {/* Rank Badge */}
                                <div className="absolute top-0 left-0 z-10 w-8 h-8">
                                    <svg viewBox="0 0 40 40" className="w-full h-full drop-shadow-lg">
                                        <path d="M0,0 H40 V30 L20,40 L0,30 Z" fill={index < 3 ? "#FFD700" : "#52525B"} />
                                        <text x="20" y="24" fontSize="18" fontWeight="bold" fill={index < 3 ? "black" : "white"} textAnchor="middle">{index + 1}</text>
                                    </svg>
                                </div>

                                {/* Cover */}
                                <div className="w-full aspect-[2/3] bg-zinc-800 rounded-xl overflow-hidden mb-3 border border-zinc-800 relative">
                                    <div className="absolute inset-0 bg-zinc-700/50 animate-pulse" /> {/* Placeholder loading */}
                                </div>

                                <h4 className="text-sm font-bold leading-tight mb-1 line-clamp-1 group-hover:text-yellow-500 transition-colors">Midnight Revenge</h4>
                                <div className="flex justify-between items-center text-[10px] text-gray-500">
                                    <span>Drama • 45 Eps</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Browse by Genre Mockup */}
                <section>
                    <div className="flex justify-between items-end mb-4">
                        <h2 className="text-xl font-bold">Browse by Genre</h2>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        {['Modern Romance', 'Suspense', 'Period Drama', 'Revenge'].map((genre) => (
                            <div key={genre} className="relative aspect-[2/1] rounded-xl overflow-hidden bg-zinc-900 border border-zinc-800 flex items-center justify-center group cursor-pointer">
                                <div className="absolute inset-0 bg-black/60 z-10 group-hover:bg-black/40 transition-all" />
                                <span className="relative z-20 font-bold text-sm text-center px-2">{genre}</span>
                            </div>
                        ))}
                    </div>
                </section>

            </div>
        </MobileLayout>
    );
}

"use client";

import { useRef, useState } from "react";
import { Play, Heart, MessageCircle, Share2, Plus, ListVideo } from "lucide-react";
import { EpisodeSheet } from "./EpisodeSheet";
import { CommentSheet } from "./CommentSheet";

export function VideoFeed() {
    const feedRef = useRef<HTMLDivElement>(null);
    const [showEpisodes, setShowEpisodes] = useState(false);
    const [showComments, setShowComments] = useState(false);

    const videos = [1, 2, 3, 4, 5];

    return (
        <>
            <div
                ref={feedRef}
                className="h-[calc(100vh-4rem)] overflow-y-scroll snap-y snap-mandatory scrollbar-hide"
            >
                {videos.map((id) => (
                    <div
                        key={id}
                        className="relative h-full w-full snap-start bg-zinc-900 border-b border-zinc-800 flex items-center justify-center"
                    >
                        {/* Video Placeholder */}
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/60 z-10" />
                        <span className="text-zinc-600 font-bold text-4xl">Video {id}</span>

                        {/* Right Sidebar Interaction */}
                        <div className="absolute right-4 bottom-24 z-20 flex flex-col items-center space-y-6">
                            <div className="relative">
                                <div className="w-10 h-10 rounded-full bg-gray-600 border border-white" />
                                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-red-500 rounded-full p-0.5">
                                    <Plus size={10} className="text-white" />
                                </div>
                            </div>

                            <div className="flex flex-col items-center space-y-1">
                                <Heart className="w-8 h-8 text-white drop-shadow-md" />
                                <span className="text-xs font-medium text-white shadow-black drop-shadow">12K</span>
                            </div>

                            <button onClick={() => setShowComments(true)} className="flex flex-col items-center space-y-1">
                                <MessageCircle className="w-8 h-8 text-white drop-shadow-md" />
                                <span className="text-xs font-medium text-white shadow-black drop-shadow">450</span>
                            </button>

                            <button onClick={() => setShowEpisodes(true)} className="flex flex-col items-center space-y-1">
                                <ListVideo className="w-8 h-8 text-white drop-shadow-md" />
                                <span className="text-xs font-medium text-white shadow-black drop-shadow">Eps</span>
                            </button>

                            <div className="flex flex-col items-center space-y-1">
                                <Share2 className="w-8 h-8 text-white drop-shadow-md" />
                                <span className="text-xs font-medium text-white shadow-black drop-shadow">Share</span>
                            </div>
                        </div>

                        {/* Bottom Info */}
                        <div className="absolute left-4 bottom-20 z-20 max-w-[75%] space-y-2">
                            <h3 className="font-bold text-white text-lg drop-shadow-md">@ChannelName</h3>
                            <p className="text-sm text-gray-200 line-clamp-2 drop-shadow-md">
                                Watching this amazing short drama! Episode {id} is so intense. #drama #short
                            </p>
                            <button
                                onClick={() => setShowEpisodes(true)}
                                className="flex items-center space-x-2 bg-white/20 px-3 py-1 rounded-full w-fit backdrop-blur-sm hover:bg-white/30 transition-colors"
                            >
                                <Play size={12} className="fill-white text-white" />
                                <span className="text-xs font-semibold text-white">Watch Full Series</span>
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            <EpisodeSheet isOpen={showEpisodes} onClose={() => setShowEpisodes(false)} />
            <CommentSheet isOpen={showComments} onClose={() => setShowComments(false)} />
        </>
    );
}

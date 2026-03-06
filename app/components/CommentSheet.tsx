"use client";

import { X, Send, ThumbsUp } from "lucide-react";
import Image from "next/image";

interface CommentSheetProps {
    isOpen: boolean;
    onClose: () => void;
}

export function CommentSheet({ isOpen, onClose }: CommentSheetProps) {
    const comments = [
        { id: 1, user: "User123", text: "This is amazing! 😍", likes: 24, time: "2m" },
        { id: 2, user: "DramaQueen", text: "Can't wait for next episode", likes: 10, time: "5m" },
        { id: 3, user: "ShortFilmLover", text: "The plot twist!!! 😱", likes: 5, time: "12m" },
    ];

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-end justify-center sm:items-center">
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />
            <div className="relative w-full max-w-md bg-zinc-900 rounded-t-3xl sm:rounded-3xl h-[60vh] flex flex-col shadow-2xl animate-in slide-in-from-bottom duration-300">

                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-zinc-800">
                    <div className="text-center w-full">
                        <h3 className="text-sm font-bold text-white">450 Comments</h3>
                    </div>
                    <button onClick={onClose} className="absolute right-4 p-1 text-gray-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                {/* List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6">
                    {comments.map((comment) => (
                        <div key={comment.id} className="flex gap-3">
                            <div className="w-8 h-8 rounded-full bg-zinc-700 shrink-0" />
                            <div className="flex-1 space-y-1">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-gray-400">{comment.user}</span>
                                    <span className="text-[10px] text-zinc-600">{comment.time}</span>
                                </div>
                                <p className="text-sm text-gray-200">{comment.text}</p>
                                <div className="flex items-center gap-4 mt-1">
                                    <button className="flex items-center gap-1 text-xs text-gray-500 hover:text-white">
                                        <ThumbsUp size={12} /> {comment.likes}
                                    </button>
                                    <button className="text-xs text-gray-500 hover:text-white">Reply</button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Input */}
                <div className="p-4 border-t border-zinc-800 bg-zinc-900 pb-safe-area-bottom">
                    <div className="flex items-center gap-2">
                        <input
                            type="text"
                            placeholder="Add a comment..."
                            className="flex-1 bg-zinc-800 rounded-full px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-yellow-500"
                        />
                        <button className="p-2.5 bg-yellow-500 rounded-full text-black hover:bg-yellow-400">
                            <Send size={16} />
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}

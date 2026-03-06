'use client';

import React, { useState, useCallback } from 'react';
import { Upload, Film, Check, X, Loader2 } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'sonner';

interface BulkUploadProps {
    dramaId: string;
    onComplete: () => void;
}

interface UploadItem {
    file: File;
    name: string;
    episodeNumber: number;
    title: string;
    status: 'pending' | 'uploading' | 'success' | 'error';
    progress: number;
    error?: string;
}

export default function BulkEpisodeUpload({ dramaId, onComplete }: BulkUploadProps) {
    const [uploads, setUploads] = useState<UploadItem[]>([]);
    const [isUploading, setIsUploading] = useState(false);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const videoFiles = acceptedFiles.filter(f => f.type.startsWith('video/'));

        // Sort by filename to maintain episode order
        const sorted = videoFiles.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));

        const items: UploadItem[] = sorted.map((file, index) => ({
            file,
            name: file.name,
            episodeNumber: index + 1,
            title: `Episode ${index + 1}`,
            status: 'pending',
            progress: 0,
        }));

        setUploads(items);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
        },
        multiple: true,
    });

    const updateUploadItem = (index: number, updates: Partial<UploadItem>) => {
        setUploads(prev => prev.map((item, i) => i === index ? { ...item, ...updates } : item));
    };

    const uploadSingle = async (item: UploadItem, index: number) => {
        updateUploadItem(index, { status: 'uploading', progress: 0 });

        try {
            // Upload video file
            const formData = new FormData();
            formData.append('file', item.file);
            formData.append('folder', 'episodes');

            const uploadRes = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!uploadRes.ok) throw new Error('Upload failed');

            const { url: videoUrl } = await uploadRes.json();
            updateUploadItem(index, { progress: 50 });

            // Create episode in database
            const episodeRes = await fetch(`/api/dramas/${dramaId}/episodes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    episodeNumber: item.episodeNumber,
                    title: item.title,
                    videoUrl,
                    description: `Episode ${item.episodeNumber}`,
                    duration: 180, // Default 3 minutes, could be extracted from video
                    isVip: item.episodeNumber > 3, // First 3 free
                    coinPrice: item.episodeNumber > 3 ? 10 : 0,
                }),
            });

            if (!episodeRes.ok) throw new Error('Failed to create episode');

            updateUploadItem(index, { status: 'success', progress: 100 });
        } catch (error: any) {
            updateUploadItem(index, { status: 'error', error: error.message });
        }
    };

    const startBulkUpload = async () => {
        setIsUploading(true);

        for (let i = 0; i < uploads.length; i++) {
            if (uploads[i].status === 'pending') {
                await uploadSingle(uploads[i], i);
            }
        }

        setIsUploading(false);

        const successCount = uploads.filter(u => u.status === 'success').length;
        if (successCount === uploads.length) {
            toast.success(`Berhasil upload ${successCount} episode!`);
            onComplete();
        } else {
            toast.warning(`${successCount}/${uploads.length} episode berhasil diupload`);
        }
    };

    const removeItem = (index: number) => {
        setUploads(prev => prev.filter((_, i) => i !== index).map((item, i) => ({
            ...item,
            episodeNumber: i + 1,
            title: `Episode ${i + 1}`,
        })));
    };

    const successCount = uploads.filter(u => u.status === 'success').length;
    const errorCount = uploads.filter(u => u.status === 'error').length;

    return (
        <div className="p-6 bg-zinc-900 rounded-xl border border-zinc-800">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Upload size={24} className="text-yellow-500" />
                Bulk Episode Upload
            </h3>

            {uploads.length === 0 ? (
                <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${isDragActive ? 'border-yellow-500 bg-yellow-500/10' : 'border-zinc-700 hover:border-zinc-600'
                        }`}
                >
                    <input {...getInputProps()} />
                    <Film size={48} className="mx-auto text-zinc-500 mb-4" />
                    <p className="text-white font-medium mb-2">
                        {isDragActive ? 'Drop files here...' : 'Drag & drop video files here'}
                    </p>
                    <p className="text-zinc-500 text-sm">
                        Supports MP4, MOV, AVI, MKV, WebM
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {/* File List */}
                    <div className="max-h-80 overflow-y-auto space-y-2">
                        {uploads.map((item, index) => (
                            <div key={index} className="flex items-center gap-4 p-3 bg-zinc-800 rounded-lg">
                                <div className="w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center">
                                    {item.status === 'pending' && <span className="text-white text-sm">{item.episodeNumber}</span>}
                                    {item.status === 'uploading' && <Loader2 size={16} className="text-yellow-500 animate-spin" />}
                                    {item.status === 'success' && <Check size={16} className="text-green-500" />}
                                    {item.status === 'error' && <X size={16} className="text-red-500" />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <input
                                        type="text"
                                        value={item.title}
                                        onChange={(e) => updateUploadItem(index, { title: e.target.value })}
                                        className="bg-transparent text-white text-sm w-full outline-none"
                                        disabled={item.status !== 'pending'}
                                    />
                                    <p className="text-zinc-500 text-xs truncate">{item.name}</p>
                                </div>
                                <span className="text-zinc-500 text-xs">
                                    {(item.file.size / (1024 * 1024)).toFixed(1)} MB
                                </span>
                                {item.status === 'pending' && (
                                    <button onClick={() => removeItem(index)} className="text-zinc-500 hover:text-red-500">
                                        <X size={16} />
                                    </button>
                                )}
                                {item.status === 'uploading' && (
                                    <span className="text-yellow-500 text-xs">{item.progress}%</span>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Stats */}
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-zinc-500">
                            {uploads.length} files selected
                            {successCount > 0 && <span className="text-green-500 ml-2">✓ {successCount} done</span>}
                            {errorCount > 0 && <span className="text-red-500 ml-2">✗ {errorCount} failed</span>}
                        </span>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setUploads([])}
                                className="px-4 py-2 bg-zinc-700 text-white rounded-lg hover:bg-zinc-600 disabled:opacity-50"
                                disabled={isUploading}
                            >
                                Reset
                            </button>
                            <button
                                onClick={startBulkUpload}
                                className="px-4 py-2 bg-yellow-500 text-black font-medium rounded-lg hover:bg-yellow-400 disabled:opacity-50 flex items-center gap-2"
                                disabled={isUploading || uploads.every(u => u.status === 'success')}
                            >
                                {isUploading ? (
                                    <>
                                        <Loader2 size={16} className="animate-spin" />
                                        Uploading...
                                    </>
                                ) : (
                                    <>
                                        <Upload size={16} />
                                        Upload All
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
    Bell, Send, CheckCircle, AlertTriangle, Megaphone,
    Film, Gift, Info, X, Search, Loader2, ChevronDown
} from 'lucide-react';

const NOTIFICATION_TYPES = [
    { value: 'system', label: 'Info Sistem', icon: Info, color: '#3b82f6' },
    { value: 'drama_baru', label: 'Drama Baru', icon: Film, color: '#10b981' },
    { value: 'promo', label: 'Promo / Event', icon: Gift, color: '#f59e0b' },
    { value: 'announcement', label: 'Pengumuman', icon: Megaphone, color: '#8b5cf6' },
];

interface Drama {
    id: string;
    title: string;
    cover: string;
    totalEpisodes: number;
    genres?: string[];
}

// ── Drama Picker ───────────────────────────────────────────────────────────────
function DramaPicker({ onSelect }: { onSelect: (d: Drama) => void }) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<Drama[]>([]);
    const [loading, setLoading] = useState(false);
    const [open, setOpen] = useState(false);
    const [selected, setSelected] = useState<Drama | null>(null);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const search = useCallback(async (q: string) => {
        if (!q.trim()) { setResults([]); return; }
        setLoading(true);
        try {
            const res = await fetch(`/api/dramas?q=${encodeURIComponent(q)}&limit=8`);
            const data = await res.json();
            setResults(data.dramas || []);
        } catch {
            setResults([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => search(query), 350);
        return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    }, [query, search]);

    // Close dropdown on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const handleSelect = (d: Drama) => {
        setSelected(d);
        setOpen(false);
        setQuery('');
        onSelect(d);
    };

    const handleClear = () => {
        setSelected(null);
        setResults([]);
        onSelect({ id: '', title: '', cover: '', totalEpisodes: 0 });
    };

    return (
        <div ref={containerRef} style={{ position: 'relative' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: 13, marginBottom: 8 }}>
                <Film size={14} />
                Pilih Drama <span style={{ color: '#64748b', fontWeight: 400 }}>(opsional — auto-isi gambar + deep link)</span>
            </label>

            {/* Selected drama pill */}
            {selected ? (
                <div style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    background: '#0f172a', borderRadius: 10, padding: '8px 12px',
                    border: '1px solid #FFD700',
                }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={selected.cover} alt="" style={{ width: 40, height: 54, objectFit: 'cover', borderRadius: 6 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: '#f1f5f9', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {selected.title}
                        </div>
                        <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                            {selected.totalEpisodes} episode · ID: {selected.id.slice(0, 12)}...
                        </div>
                    </div>
                    <button onClick={handleClear} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', padding: 4 }}>
                        <X size={16} />
                    </button>
                </div>
            ) : (
                /* Search input */
                <div style={{ position: 'relative' }}>
                    <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
                    <input
                        type="text"
                        value={query}
                        onChange={e => { setQuery(e.target.value); setOpen(true); }}
                        onFocus={() => setOpen(true)}
                        placeholder="Ketik judul drama untuk mencari..."
                        style={{
                            width: '100%', padding: '10px 14px 10px 34px',
                            borderRadius: 10, border: '1px solid #334155',
                            background: '#0f172a', color: '#e2e8f0',
                            fontSize: 13, outline: 'none', boxSizing: 'border-box',
                        }}
                    />
                    {loading && (
                        <Loader2 size={14} style={{
                            position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                            color: '#64748b', animation: 'spin 0.8s linear infinite',
                        }} />
                    )}
                </div>
            )}

            {/* Dropdown results */}
            {open && !selected && results.length > 0 && (
                <div style={{
                    position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50,
                    background: '#1e293b', border: '1px solid #334155', borderRadius: 12,
                    marginTop: 4, maxHeight: 320, overflowY: 'auto',
                    boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
                }}>
                    {results.map(d => (
                        <button
                            key={d.id}
                            onClick={() => handleSelect(d)}
                            style={{
                                width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                                padding: '10px 14px', background: 'none', border: 'none',
                                cursor: 'pointer', textAlign: 'left', transition: 'background 0.15s',
                                borderBottom: '1px solid #0f172a',
                            }}
                            onMouseEnter={e => (e.currentTarget.style.background = '#334155')}
                            onMouseLeave={e => (e.currentTarget.style.background = 'none')}
                        >
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={d.cover} alt="" style={{ width: 36, height: 48, objectFit: 'cover', borderRadius: 6, flexShrink: 0 }} />
                            <div style={{ minWidth: 0 }}>
                                <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {d.title}
                                </div>
                                <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                                    {d.totalEpisodes} episode
                                </div>
                            </div>
                        </button>
                    ))}
                </div>
            )}

            {open && !selected && query.trim() && !loading && results.length === 0 && (
                <div style={{
                    position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50,
                    background: '#1e293b', border: '1px solid #334155', borderRadius: 12,
                    marginTop: 4, padding: '16px', textAlign: 'center',
                    color: '#64748b', fontSize: 13,
                }}>
                    Tidak ada drama ditemukan untuk &quot;{query}&quot;
                </div>
            )}
        </div>
    );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function BroadcastNotificationPage() {
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [type, setType] = useState('system');
    const [imageUrl, setImageUrl] = useState('');
    const [dramaId, setDramaId] = useState('');
    const [episodeNumber, setEpisodeNumber] = useState('1');
    const [selectedDrama, setSelectedDrama] = useState<Drama | null>(null);
    const [sending, setSending] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');

    const selectedType = NOTIFICATION_TYPES.find(t => t.value === type) || NOTIFICATION_TYPES[0];

    const handleDramaSelect = (d: Drama) => {
        if (!d.id) {
            // cleared
            setSelectedDrama(null);
            setImageUrl('');
            setDramaId('');
            setEpisodeNumber('1');
            return;
        }
        setSelectedDrama(d);
        setImageUrl(d.cover);
        setDramaId(d.id);
        setEpisodeNumber('1');
        // Auto-suggest title if empty
        if (!title.trim()) setTitle(`🎬 ${d.title}`);
    };

    const handleSend = async () => {
        if (!title.trim() || !body.trim()) {
            setError('Judul dan isi pesan wajib diisi');
            return;
        }
        setSending(true);
        setError('');
        setResult(null);

        try {
            const payload: any = { title: title.trim(), body: body.trim(), type };
            if (imageUrl.trim()) payload.imageUrl = imageUrl.trim();
            if (dramaId.trim()) payload.dramaId = dramaId.trim();
            if (dramaId.trim() && episodeNumber) payload.episodeNumber = episodeNumber;

            const res = await fetch('/api/notifications/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Gagal mengirim');

            setResult(data);
            setTitle('');
            setBody('');
            setImageUrl('');
            setDramaId('');
            setEpisodeNumber('1');
            setSelectedDrama(null);
        } catch (e: any) {
            setError(e.message || 'Gagal mengirim notifikasi');
        } finally {
            setSending(false);
        }
    };

    return (
        <div style={{ padding: '32px', maxWidth: 900, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
                <div style={{
                    width: 48, height: 48, borderRadius: 12,
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                    <Megaphone size={24} color="white" />
                </div>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                        Broadcast Notifikasi
                    </h1>
                    <p style={{ color: '#94a3b8', margin: 0, fontSize: 14 }}>
                        Kirim rich push notification ke semua perangkat pengguna
                    </p>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 24 }}>
                {/* ── Form ── */}
                <div style={{
                    background: '#1e293b', borderRadius: 16, padding: 24,
                    border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: 20,
                }}>

                    {/* Type */}
                    <div>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 8 }}>Tipe Notifikasi</label>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                            {NOTIFICATION_TYPES.map(t => {
                                const Icon = t.icon;
                                const isSelected = type === t.value;
                                return (
                                    <button key={t.value} onClick={() => setType(t.value)} style={{
                                        padding: '10px 8px', borderRadius: 10, border: 'none',
                                        background: isSelected ? `${t.color}20` : '#0f172a',
                                        outline: isSelected ? `2px solid ${t.color}` : '1px solid #334155',
                                        cursor: 'pointer', display: 'flex', flexDirection: 'column',
                                        alignItems: 'center', gap: 6, transition: 'all 0.2s',
                                    }}>
                                        <Icon size={18} color={isSelected ? t.color : '#64748b'} />
                                        <span style={{ fontSize: 11, color: isSelected ? t.color : '#94a3b8', fontWeight: isSelected ? 600 : 400 }}>
                                            {t.label}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* ★ Drama Picker */}
                    <DramaPicker onSelect={handleDramaSelect} />

                    {/* Episode number — only show if drama selected */}
                    {selectedDrama && (
                        <div>
                            <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>
                                Mulai dari Episode
                            </label>
                            <input
                                type="number" value={episodeNumber} min={1}
                                max={selectedDrama.totalEpisodes || 999}
                                onChange={e => setEpisodeNumber(e.target.value)}
                                style={{
                                    width: 120, padding: '8px 12px', borderRadius: 8,
                                    border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0',
                                    fontSize: 13, outline: 'none',
                                }}
                            />
                            <span style={{ color: '#64748b', fontSize: 12, marginLeft: 10 }}>
                                dari {selectedDrama.totalEpisodes} episode
                            </span>
                        </div>
                    )}

                    {/* Title */}
                    <div>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>
                            Judul <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <input
                            type="text" value={title} onChange={e => setTitle(e.target.value)}
                            placeholder="Contoh: 🎬 Drama Baru Telah Hadir!"
                            maxLength={100}
                            style={{
                                width: '100%', padding: '10px 14px', borderRadius: 10,
                                border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0',
                                fontSize: 14, outline: 'none', boxSizing: 'border-box',
                            }}
                        />
                        <span style={{ float: 'right', fontSize: 11, color: '#64748b', marginTop: 4 }}>
                            {title.length}/100
                        </span>
                    </div>

                    {/* Body */}
                    <div>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>
                            Isi Pesan <span style={{ color: '#ef4444' }}>*</span>
                        </label>
                        <textarea
                            value={body} onChange={e => setBody(e.target.value)}
                            placeholder="Tulis pesan untuk semua pengguna..."
                            maxLength={500} rows={3}
                            style={{
                                width: '100%', padding: '10px 14px', borderRadius: 10,
                                border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0',
                                fontSize: 14, outline: 'none', resize: 'vertical', boxSizing: 'border-box',
                                fontFamily: 'inherit',
                            }}
                        />
                        <span style={{ float: 'right', fontSize: 11, color: '#64748b', marginTop: 4 }}>
                            {body.length}/500
                        </span>
                    </div>

                    {/* Manual image URL override (collapsed by default) */}
                    {!selectedDrama && (
                        <div>
                            <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>
                                URL Gambar Manual <span style={{ color: '#64748b', fontWeight: 400 }}>(jika tidak pilih drama)</span>
                            </label>
                            <input
                                type="text" value={imageUrl}
                                onChange={e => setImageUrl(e.target.value)}
                                placeholder="https://cdn.shortlovers.id/cover/drama.jpg"
                                style={{
                                    width: '100%', padding: '10px 14px', borderRadius: 10,
                                    border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0',
                                    fontSize: 13, outline: 'none', boxSizing: 'border-box',
                                }}
                            />
                        </div>
                    )}

                    {/* Error / Success */}
                    {error && (
                        <div style={{
                            padding: '10px 14px', borderRadius: 10,
                            background: '#dc262620', border: '1px solid #dc2626',
                            color: '#fca5a5', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8,
                        }}>
                            <AlertTriangle size={16} /> {error}
                        </div>
                    )}
                    {result && (
                        <div style={{
                            padding: '14px', borderRadius: 10,
                            background: '#10b98120', border: '1px solid #10b981', color: '#6ee7b7', fontSize: 13,
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                <CheckCircle size={16} /> Notifikasi berhasil dikirim!
                            </div>
                            <div style={{ color: '#94a3b8', fontSize: 12 }}>
                                📱 In-app: <strong>{result.inApp}</strong> user &nbsp;|&nbsp;
                                🔔 Push: <strong style={{ color: '#6ee7b7' }}>{result.push?.sent || 0}</strong> terkirim
                                {result.push?.failed > 0 && (
                                    <span style={{ color: '#fca5a5', marginLeft: 6 }}>· {result.push.failed} gagal</span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Send button */}
                    <button
                        onClick={handleSend}
                        disabled={sending || !title.trim() || !body.trim()}
                        style={{
                            width: '100%', padding: '13px 24px', borderRadius: 12, border: 'none',
                            cursor: sending ? 'not-allowed' : 'pointer',
                            background: sending ? '#334155' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            color: 'white', fontSize: 15, fontWeight: 600,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                            opacity: (!title.trim() || !body.trim()) ? 0.5 : 1,
                            transition: 'all 0.2s',
                        }}
                    >
                        {sending ? (
                            <><Loader2 size={18} style={{ animation: 'spin 0.8s linear infinite' }} /> Mengirim ke semua perangkat...</>
                        ) : (
                            <><Send size={18} /> Kirim ke Semua Perangkat</>
                        )}
                    </button>
                </div>

                {/* ── Preview ── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div style={{
                        background: '#1e293b', borderRadius: 16, padding: 20,
                        border: '1px solid #334155',
                    }}>
                        <h3 style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8', margin: '0 0 14px' }}>
                            📱 Preview Notifikasi Android
                        </h3>

                        <div style={{
                            background: '#1a1a2e', borderRadius: 12, padding: '10px 12px',
                            border: '1px solid #334155',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                                <div style={{
                                    width: 16, height: 16, borderRadius: 3, background: '#FFD700',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    <Bell size={10} color="#000" />
                                </div>
                                <span style={{ fontSize: 10, color: '#94a3b8', fontWeight: 600 }}>KingShort</span>
                                <span style={{ fontSize: 9, color: '#64748b', marginLeft: 'auto' }}>sekarang</span>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <div style={{ fontSize: 12, fontWeight: 700, color: title ? '#f1f5f9' : '#475569', marginBottom: 2, lineHeight: 1.3 }}>
                                        {title || 'Judul notifikasi...'}
                                    </div>
                                    <div style={{
                                        fontSize: 11, color: body ? '#94a3b8' : '#334155', lineHeight: 1.4,
                                        overflow: 'hidden', display: '-webkit-box',
                                        WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                                    }}>
                                        {body || 'Isi pesan akan tampil di sini...'}
                                    </div>
                                </div>

                                {/* Thumbnail — pojok kanan */}
                                <div style={{
                                    width: 44, height: 58, borderRadius: 6, overflow: 'hidden', flexShrink: 0,
                                    background: '#0f172a', border: '1px solid #334155',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    {imageUrl ? (
                                        // eslint-disable-next-line @next/next/no-img-element
                                        <img src={imageUrl} alt="cover" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                    ) : (
                                        <Film size={18} color="#334155" />
                                    )}
                                </div>
                            </div>
                        </div>

                        <p style={{ fontSize: 10, color: '#475569', margin: '10px 0 0', lineHeight: 1.6 }}>
                            Pilih drama di atas → gambar cover otomatis terisi sebagai thumbnail
                        </p>
                    </div>

                    {/* Info card */}
                    <div style={{
                        background: '#0f172a', borderRadius: 12, padding: 14,
                        border: '1px solid #1e293b', fontSize: 12, color: '#64748b', lineHeight: 1.8,
                    }}>
                        <div style={{ color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>ℹ️ Cara Kirim</div>
                        <div>1. Pilih drama dari kolom pencarian</div>
                        <div>2. Gambar & drama ID terisi otomatis</div>
                        <div>3. Tulis judul &amp; isi pesan</div>
                        <div>4. Klik <strong style={{ color: '#8b5cf6' }}>Kirim ke Semua Perangkat</strong></div>
                        <div style={{ marginTop: 8, color: '#475569' }}>
                            Klik notif di HP → langsung buka drama episode {episodeNumber || '1'}
                        </div>
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                input::placeholder, textarea::placeholder { color: #475569; }
                * { scrollbar-width: thin; scrollbar-color: #334155 transparent; }
            `}</style>
        </div>
    );
}

'use client';

import { useState } from 'react';
import { Bell, Send, CheckCircle, AlertTriangle, Megaphone, Film, Gift, Info, Image, X } from 'lucide-react';

const NOTIFICATION_TYPES = [
    { value: 'system', label: 'Info Sistem', icon: Info, color: '#3b82f6' },
    { value: 'drama_baru', label: 'Drama Baru', icon: Film, color: '#10b981' },
    { value: 'promo', label: 'Promo / Event', icon: Gift, color: '#f59e0b' },
    { value: 'announcement', label: 'Pengumuman', icon: Megaphone, color: '#8b5cf6' },
];

export default function BroadcastNotificationPage() {
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [type, setType] = useState('system');
    const [imageUrl, setImageUrl] = useState('');
    const [dramaId, setDramaId] = useState('');
    const [episodeNumber, setEpisodeNumber] = useState('1');
    const [sending, setSending] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');
    const [imgError, setImgError] = useState(false);

    const selectedType = NOTIFICATION_TYPES.find(t => t.value === type) || NOTIFICATION_TYPES[0];

    const handleSend = async () => {
        if (!title.trim() || !body.trim()) {
            setError('Judul dan isi pesan wajib diisi');
            return;
        }

        setSending(true);
        setError('');
        setResult(null);

        try {
            const payload: any = {
                title: title.trim(),
                body: body.trim(),
                type,
            };
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
        } catch (e: any) {
            setError(e.message || 'Gagal mengirim notifikasi');
        } finally {
            setSending(false);
        }
    };

    const validImage = imageUrl.trim() && !imgError;

    return (
        <div style={{ padding: '32px', maxWidth: 860, margin: '0 auto' }}>
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
                        Kirim notifikasi rich push (dengan gambar) ke semua perangkat pengguna
                    </p>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 24 }}>
                {/* ── Compose Form ── */}
                <div style={{
                    background: '#1e293b', borderRadius: 16, padding: 24,
                    border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: 18,
                }}>
                    <h2 style={{ fontSize: 16, fontWeight: 600, color: '#e2e8f0', margin: 0 }}>
                        Tulis Pesan
                    </h2>

                    {/* Type */}
                    <div>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 8 }}>
                            Tipe Notifikasi
                        </label>
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

                    {/* Image URL */}
                    <div>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>
                            <Image size={14} />
                            URL Gambar Thumbnail <span style={{ color: '#64748b', fontWeight: 400 }}>(opsional — tampil di pojok kanan notifikasi)</span>
                        </label>
                        <div style={{ position: 'relative' }}>
                            <input
                                type="text" value={imageUrl}
                                onChange={e => { setImageUrl(e.target.value); setImgError(false); }}
                                placeholder="https://cdn.shortlovers.id/cover/drama.jpg"
                                style={{
                                    width: '100%', padding: '10px 14px', borderRadius: 10,
                                    border: `1px solid ${imageUrl && imgError ? '#ef4444' : '#334155'}`,
                                    background: '#0f172a', color: '#e2e8f0',
                                    fontSize: 13, outline: 'none', boxSizing: 'border-box',
                                }}
                            />
                            {imageUrl && (
                                <button onClick={() => { setImageUrl(''); setImgError(false); }} style={{
                                    position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                                    background: 'none', border: 'none', cursor: 'pointer', color: '#64748b',
                                }}>
                                    <X size={14} />
                                </button>
                            )}
                        </div>
                        {imageUrl && imgError && (
                            <p style={{ margin: '4px 0 0', fontSize: 11, color: '#ef4444' }}>
                                ⚠️ Gambar tidak bisa dimuat — pastikan URL valid dan publik
                            </p>
                        )}
                    </div>

                    {/* Drama deep-link */}
                    <div style={{
                        background: '#0f172a', borderRadius: 10, padding: 14,
                        border: '1px solid #1e293b',
                    }}>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 10 }}>
                            🎬 Deep Link Drama <span style={{ color: '#64748b', fontWeight: 400 }}>(opsional — klik notif langsung buka drama)</span>
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8 }}>
                            <div>
                                <label style={{ display: 'block', color: '#64748b', fontSize: 11, marginBottom: 4 }}>Drama ID</label>
                                <input
                                    type="text" value={dramaId} onChange={e => setDramaId(e.target.value)}
                                    placeholder="cuid drama..."
                                    style={{
                                        width: '100%', padding: '8px 12px', borderRadius: 8,
                                        border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0',
                                        fontSize: 12, outline: 'none', boxSizing: 'border-box',
                                    }}
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', color: '#64748b', fontSize: 11, marginBottom: 4 }}>Episode</label>
                                <input
                                    type="number" value={episodeNumber}
                                    onChange={e => setEpisodeNumber(e.target.value)}
                                    min={1} placeholder="1"
                                    style={{
                                        width: '100%', padding: '8px 12px', borderRadius: 8,
                                        border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0',
                                        fontSize: 12, outline: 'none', boxSizing: 'border-box',
                                    }}
                                />
                            </div>
                        </div>
                    </div>

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
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                <CheckCircle size={16} /> Notifikasi berhasil dikirim!
                            </div>
                            <div style={{ color: '#94a3b8', fontSize: 12 }}>
                                📱 In-app: <strong>{result.inApp}</strong> user &nbsp;|&nbsp;
                                🔔 Push dikirim: <strong style={{ color: '#6ee7b7' }}>{result.push?.sent || 0}</strong>&nbsp;
                                {result.push?.failed > 0 && (
                                    <span style={{ color: '#fca5a5' }}>✗ {result.push.failed} gagal</span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Send */}
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
                            <>
                                <span style={{
                                    width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)',
                                    borderTop: '2px solid white', borderRadius: '50%',
                                    animation: 'spin 0.8s linear infinite', display: 'inline-block',
                                }} />
                                Mengirim ke semua perangkat...
                            </>
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
                        <h3 style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8', marginBottom: 14, margin: '0 0 14px' }}>
                            📱 Preview Notifikasi Android
                        </h3>

                        {/* Android notification card */}
                        <div style={{
                            background: '#1a1a2e', borderRadius: 12, padding: '10px 12px',
                            border: '1px solid #334155',
                        }}>
                            {/* App name row */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                                <div style={{
                                    width: 16, height: 16, borderRadius: 3,
                                    background: '#FFD700', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    <Bell size={10} color="#000" />
                                </div>
                                <span style={{ fontSize: 10, color: '#94a3b8', fontWeight: 600 }}>KingShort</span>
                                <span style={{ fontSize: 9, color: '#64748b', marginLeft: 'auto' }}>sekarang</span>
                            </div>

                            {/* Title + Thumbnail row */}
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <div style={{
                                        fontSize: 12, fontWeight: 700,
                                        color: title ? '#f1f5f9' : '#475569',
                                        marginBottom: 2, lineHeight: 1.3,
                                    }}>
                                        {title || 'Judul notifikasi...'}
                                    </div>
                                    <div style={{
                                        fontSize: 11, color: body ? '#94a3b8' : '#334155',
                                        lineHeight: 1.4,
                                        overflow: 'hidden',
                                        display: '-webkit-box',
                                        WebkitLineClamp: 2,
                                        WebkitBoxOrient: 'vertical',
                                    }}>
                                        {body || 'Isi pesan akan muncul di sini...'}
                                    </div>
                                </div>

                                {/* Thumbnail — pojok kanan (the key feature) */}
                                <div style={{
                                    width: 44, height: 44, borderRadius: 6, overflow: 'hidden',
                                    flexShrink: 0, background: '#0f172a',
                                    border: `1px solid ${validImage ? '#334155' : '#1e293b'}`,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    {validImage ? (
                                        <img
                                            src={imageUrl}
                                            alt="thumbnail"
                                            onError={() => setImgError(true)}
                                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                        />
                                    ) : (
                                        <Image size={18} color="#334155" />
                                    )}
                                </div>
                            </div>
                        </div>

                        <p style={{ fontSize: 10, color: '#475569', margin: '10px 0 0', lineHeight: 1.6 }}>
                            Gambar di kanan = thumbnail drama seperti FreeReels & HotMiniDrama.
                            Gunakan URL cover drama dari R2 / CDN.
                        </p>
                    </div>

                    {/* Info card */}
                    <div style={{
                        background: '#0f172a', borderRadius: 12, padding: 14,
                        border: '1px solid #1e293b', fontSize: 12, color: '#64748b', lineHeight: 1.7,
                    }}>
                        <div style={{ color: '#94a3b8', fontWeight: 600, marginBottom: 8 }}>ℹ️ Cara Pakai</div>
                        <div>1. Isi Judul + Pesan</div>
                        <div>2. Paste URL cover drama di kolom gambar</div>
                        <div>3. (Opsional) Isi Drama ID agar klik langsung buka drama</div>
                        <div>4. Klik Kirim — notif dikirim ke semua perangkat</div>
                    </div>
                </div>
            </div>

            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
    );
}

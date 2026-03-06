'use client';

import { useState } from 'react';
import { Bell, Send, CheckCircle, AlertTriangle, Megaphone, Film, Gift, Info } from 'lucide-react';

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
    const [sending, setSending] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState('');

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
            const res = await fetch('/api/notifications/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title.trim(), body: body.trim(), type }),
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Gagal mengirim');

            setResult(data);
            setTitle('');
            setBody('');
        } catch (e: any) {
            setError(e.message || 'Gagal mengirim notifikasi');
        } finally {
            setSending(false);
        }
    };

    return (
        <div style={{ padding: '32px', maxWidth: 800, margin: '0 auto' }}>
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
                        Kirim notifikasi push ke semua pengguna
                    </p>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24 }}>
                {/* Compose Form */}
                <div style={{
                    background: '#1e293b', borderRadius: 16, padding: 24,
                    border: '1px solid #334155',
                }}>
                    <h2 style={{ fontSize: 16, fontWeight: 600, color: '#e2e8f0', marginBottom: 20 }}>
                        Tulis Pesan
                    </h2>

                    {/* Type Selector */}
                    <div style={{ marginBottom: 20 }}>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 8 }}>
                            Tipe Notifikasi
                        </label>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                            {NOTIFICATION_TYPES.map(t => {
                                const Icon = t.icon;
                                const isSelected = type === t.value;
                                return (
                                    <button
                                        key={t.value}
                                        onClick={() => setType(t.value)}
                                        style={{
                                            padding: '10px 8px', borderRadius: 10, border: 'none',
                                            background: isSelected ? `${t.color}20` : '#0f172a',
                                            outline: isSelected ? `2px solid ${t.color}` : '1px solid #334155',
                                            cursor: 'pointer', display: 'flex', flexDirection: 'column',
                                            alignItems: 'center', gap: 6, transition: 'all 0.2s',
                                        }}
                                    >
                                        <Icon size={18} color={isSelected ? t.color : '#64748b'} />
                                        <span style={{
                                            fontSize: 11, color: isSelected ? t.color : '#94a3b8',
                                            fontWeight: isSelected ? 600 : 400,
                                        }}>
                                            {t.label}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Title Input */}
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>
                            Judul
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Contoh: Drama Baru Minggu Ini!"
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

                    {/* Body Input */}
                    <div style={{ marginBottom: 20 }}>
                        <label style={{ display: 'block', color: '#94a3b8', fontSize: 13, marginBottom: 6 }}>
                            Isi Pesan
                        </label>
                        <textarea
                            value={body}
                            onChange={(e) => setBody(e.target.value)}
                            placeholder="Tulis pesan yang ingin dikirim ke semua pengguna..."
                            maxLength={500}
                            rows={4}
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

                    {/* Error */}
                    {error && (
                        <div style={{
                            padding: '10px 14px', borderRadius: 10, marginBottom: 16,
                            background: '#dc262620', border: '1px solid #dc2626',
                            color: '#fca5a5', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8,
                        }}>
                            <AlertTriangle size={16} /> {error}
                        </div>
                    )}

                    {/* Success */}
                    {result && (
                        <div style={{
                            padding: '14px', borderRadius: 10, marginBottom: 16,
                            background: '#10b98120', border: '1px solid #10b981',
                            color: '#6ee7b7', fontSize: 13,
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                <CheckCircle size={16} /> Notifikasi berhasil dikirim!
                            </div>
                            <div style={{ color: '#94a3b8', fontSize: 12 }}>
                                📱 In-app: {result.inApp} user &nbsp;|&nbsp;
                                🔔 Push: {result.push?.sent || 0} terkirim, {result.push?.failed || 0} gagal
                            </div>
                        </div>
                    )}

                    {/* Send Button */}
                    <button
                        onClick={handleSend}
                        disabled={sending || !title.trim() || !body.trim()}
                        style={{
                            width: '100%', padding: '12px 24px', borderRadius: 12,
                            border: 'none', cursor: sending ? 'not-allowed' : 'pointer',
                            background: sending ? '#334155' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            color: 'white', fontSize: 15, fontWeight: 600,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                            opacity: (!title.trim() || !body.trim()) ? 0.5 : 1,
                            transition: 'all 0.2s',
                        }}
                    >
                        {sending ? (
                            <>Mengirim...</>
                        ) : (
                            <><Send size={18} /> Kirim ke Semua User</>
                        )}
                    </button>
                </div>

                {/* Preview Card */}
                <div>
                    <div style={{
                        background: '#1e293b', borderRadius: 16, padding: 20,
                        border: '1px solid #334155',
                    }}>
                        <h3 style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 16 }}>
                            📱 Preview Notifikasi
                        </h3>

                        {/* Phone notification preview */}
                        <div style={{
                            background: '#0f172a', borderRadius: 12, padding: 14,
                            border: '1px solid #1e293b',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                                <div style={{
                                    width: 28, height: 28, borderRadius: 6,
                                    background: selectedType.color + '30',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    <Bell size={14} color={selectedType.color} />
                                </div>
                                <div>
                                    <span style={{ fontSize: 11, color: '#64748b' }}>KingShort</span>
                                    <span style={{ fontSize: 10, color: '#475569', marginLeft: 8 }}>sekarang</span>
                                </div>
                            </div>
                            <div style={{
                                fontSize: 13, fontWeight: 600,
                                color: title ? '#e2e8f0' : '#475569',
                                marginBottom: 4,
                            }}>
                                {title || 'Judul notifikasi...'}
                            </div>
                            <div style={{
                                fontSize: 12, color: body ? '#94a3b8' : '#334155',
                                lineHeight: 1.4,
                                overflow: 'hidden',
                                display: '-webkit-box',
                                WebkitLineClamp: 3,
                                WebkitBoxOrient: 'vertical',
                            }}>
                                {body || 'Isi pesan notifikasi akan muncul di sini...'}
                            </div>
                        </div>

                        <div style={{
                            marginTop: 16, padding: '10px 12px', borderRadius: 8,
                            background: '#0f172a', fontSize: 12, color: '#64748b',
                        }}>
                            <div>Tipe: <span style={{ color: selectedType.color }}>{selectedType.label}</span></div>
                            <div style={{ marginTop: 4 }}>Target: Semua pengguna aktif</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

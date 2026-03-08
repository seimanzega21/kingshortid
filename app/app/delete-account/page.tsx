import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Hapus Akun — KingShort",
    description: "Halaman penghapusan akun KingShort",
};

export default function DeleteAccountPage() {
    return (
        <div style={{
            minHeight: '100vh',
            backgroundColor: '#0a0a0a',
            color: '#e5e5e5',
            padding: '40px 20px',
            fontFamily: 'var(--font-geist-sans), system-ui, sans-serif',
        }}>
            <div style={{ maxWidth: 720, margin: '0 auto' }}>
                <h1 style={{ color: '#FFD700', fontSize: 28, fontWeight: 'bold', marginBottom: 8 }}>
                    Penghapusan Akun
                </h1>
                <p style={{ color: '#9CA3AF', fontSize: 14, marginBottom: 32 }}>
                    Terakhir diperbarui: 8 Maret 2026
                </p>

                <Section title="Cara Menghapus Akun">
                    Anda dapat menghapus akun KingShort Anda dengan mengikuti langkah-langkah berikut:
                    <ol style={{ paddingLeft: 20, lineHeight: 2, marginTop: 12 }}>
                        <li>Buka aplikasi <strong>KingShort</strong></li>
                        <li>Masuk ke tab <strong>Profil</strong></li>
                        <li>Ketuk <strong>Pengaturan</strong> (ikon ⚙️)</li>
                        <li>Scroll ke bawah dan ketuk <strong>&quot;Hapus Akun&quot;</strong></li>
                        <li>Konfirmasi penghapusan akun Anda</li>
                    </ol>
                </Section>

                <Section title="Melalui Email">
                    Jika Anda tidak dapat mengakses aplikasi, Anda dapat meminta penghapusan akun
                    dengan mengirim email ke:
                    <br /><br />
                    📧 <a href="mailto:cs.kingshort@gmail.com" style={{ color: '#FFD700' }}>cs.kingshort@gmail.com</a>
                    <br /><br />
                    Sertakan informasi berikut dalam email Anda:
                    <ul style={{ paddingLeft: 20, lineHeight: 1.8, marginTop: 8 }}>
                        <li>Alamat email yang terdaftar di akun KingShort Anda</li>
                        <li>Alasan penghapusan (opsional)</li>
                    </ul>
                </Section>

                <Section title="Data yang Akan Dihapus">
                    Saat Anda menghapus akun, data berikut akan dihapus secara permanen:
                    <ul style={{ paddingLeft: 20, lineHeight: 1.8, marginTop: 8 }}>
                        <li><strong>Profil pengguna</strong> — nama, email, foto profil</li>
                        <li><strong>Saldo koin</strong> — semua koin yang belum digunakan</li>
                        <li><strong>Riwayat tontonan</strong> — daftar episode yang pernah ditonton</li>
                        <li><strong>Data check-in</strong> — streak dan riwayat check-in harian</li>
                        <li><strong>Riwayat transaksi</strong> — semua log transaksi koin</li>
                        <li><strong>Daftar bookmark</strong> — drama yang disimpan</li>
                    </ul>
                </Section>

                <Section title="Waktu Pemrosesan">
                    Penghapusan akun akan diproses dalam waktu <strong>maksimal 7 hari kerja</strong> setelah
                    permintaan dikonfirmasi. Setelah dihapus, data tidak dapat dipulihkan.
                </Section>

                <Section title="Hubungi Kami">
                    Jika Anda memiliki pertanyaan tentang penghapusan akun, hubungi kami di:
                    <br /><br />
                    📧 <a href="mailto:cs.kingshort@gmail.com" style={{ color: '#FFD700' }}>cs.kingshort@gmail.com</a>
                </Section>

                <div style={{ borderTop: '1px solid #333', marginTop: 48, paddingTop: 24, textAlign: 'center' }}>
                    <p style={{ color: '#666', fontSize: 13 }}>
                        © 2026 KingShort. All rights reserved.
                    </p>
                </div>
            </div>
        </div>
    );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div style={{ marginBottom: 32 }}>
            <h2 style={{ color: '#FFFFFF', fontSize: 18, fontWeight: '600', marginBottom: 12 }}>
                {title}
            </h2>
            <div style={{ color: '#d1d5db', fontSize: 15, lineHeight: 1.7 }}>
                {children}
            </div>
        </div>
    );
}

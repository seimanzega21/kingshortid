import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Kebijakan Privasi — KingShort",
    description: "Kebijakan privasi aplikasi KingShort",
};

export default function PrivacyPolicyPage() {
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
                    Kebijakan Privasi
                </h1>
                <p style={{ color: '#9CA3AF', fontSize: 14, marginBottom: 32 }}>
                    Terakhir diperbarui: 21 Februari 2026
                </p>

                <Section title="1. Pendahuluan">
                    KingShort (&quot;kami&quot;, &quot;aplikasi&quot;) berkomitmen melindungi privasi pengguna.
                    Kebijakan ini menjelaskan bagaimana kami mengumpulkan, menggunakan, dan melindungi
                    informasi Anda saat menggunakan aplikasi KingShort.
                </Section>

                <Section title="2. Data yang Kami Kumpulkan">
                    <ul style={{ paddingLeft: 20, lineHeight: 1.8 }}>
                        <li><strong>Informasi Akun:</strong> Email dan kata sandi (jika mendaftar). Akun tamu menggunakan ID perangkat anonim.</li>
                        <li><strong>Data Penggunaan:</strong> Riwayat tontonan, episode yang ditonton, dan preferensi konten untuk personalisasi.</li>
                        <li><strong>Device ID:</strong> Identifikasi perangkat anonim untuk login tamu dan fungsionalitas aplikasi.</li>
                        <li><strong>Push Notification Token:</strong> Token perangkat untuk mengirim notifikasi (opsional, bisa dinonaktifkan).</li>
                    </ul>
                </Section>

                <Section title="3. Bagaimana Kami Menggunakan Data">
                    <ul style={{ paddingLeft: 20, lineHeight: 1.8 }}>
                        <li>Menyediakan dan meningkatkan layanan streaming</li>
                        <li>Personalisasi rekomendasi konten</li>
                        <li>Mengelola akun pengguna dan sistem koin</li>
                        <li>Mengirim notifikasi tentang konten baru (jika diizinkan)</li>
                        <li>Analitik internal untuk peningkatan aplikasi</li>
                    </ul>
                </Section>

                <Section title="4. Penyimpanan dan Keamanan Data">
                    Data Anda disimpan dengan aman menggunakan enkripsi standar industri.
                    Token autentikasi disimpan secara lokal di perangkat Anda menggunakan penyimpanan aman (Secure Store).
                    Kami tidak menjual atau membagikan data pribadi Anda kepada pihak ketiga untuk tujuan pemasaran.
                </Section>

                <Section title="5. Hak Pengguna">
                    <ul style={{ paddingLeft: 20, lineHeight: 1.8 }}>
                        <li><strong>Akses:</strong> Anda dapat melihat data profil Anda di pengaturan aplikasi.</li>
                        <li><strong>Penghapusan:</strong> Anda dapat menghapus akun dan semua data terkait dengan menghubungi kami.</li>
                        <li><strong>Notifikasi:</strong> Anda dapat menonaktifkan notifikasi kapan saja melalui pengaturan.</li>
                        <li><strong>Riwayat:</strong> Anda dapat menghapus riwayat tontonan dari halaman Daftar Saya.</li>
                    </ul>
                </Section>

                <Section title="6. Layanan Pihak Ketiga">
                    Aplikasi dapat menggunakan layanan pihak ketiga berikut:
                    <ul style={{ paddingLeft: 20, lineHeight: 1.8, marginTop: 8 }}>
                        <li>Google Sign-In — untuk autentikasi</li>
                        <li>Expo Push Notifications — untuk notifikasi</li>
                        <li>Cloudflare — untuk hosting dan CDN</li>
                    </ul>
                    Setiap layanan memiliki kebijakan privasi mereka sendiri.
                </Section>

                <Section title="7. Anak-Anak">
                    KingShort tidak ditujukan untuk anak di bawah 13 tahun.
                    Kami tidak secara sengaja mengumpulkan data dari anak-anak.
                    Jika Anda mengetahui bahwa anak di bawah 13 tahun telah memberikan data pribadi kepada kami,
                    silakan hubungi kami untuk penghapusan.
                </Section>

                <Section title="8. Perubahan Kebijakan">
                    Kami dapat memperbarui kebijakan ini dari waktu ke waktu.
                    Perubahan akan diberitahukan melalui aplikasi atau halaman ini.
                    Penggunaan aplikasi setelah perubahan berarti Anda menyetujui kebijakan yang diperbarui.
                </Section>

                <Section title="9. Hubungi Kami">
                    Jika Anda memiliki pertanyaan tentang kebijakan privasi ini, hubungi kami di:
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

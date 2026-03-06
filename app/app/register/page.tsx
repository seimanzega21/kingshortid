import Link from "next/link";
import { ChevronLeft, User, Mail, Lock } from "lucide-react";

export default function RegisterPage() {
    return (
        <div className="min-h-screen bg-black text-white flex flex-col px-6 py-8">
            {/* Header */}
            <div className="flex items-center mb-6">
                <Link href="/welcome" className="p-2 -ml-2 text-gray-400 hover:text-white">
                    <ChevronLeft size={28} />
                </Link>
            </div>

            {/* Title */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-yellow-500 mb-2">Buat Akun Baru</h1>
                <p className="text-gray-400">Bergabunglah untuk akses penuh.</p>
            </div>

            {/* Form */}
            <form className="space-y-5">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300 ml-1">Nama Lengkap</label>
                    <div className="relative">
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                            <User size={20} />
                        </div>
                        <input
                            type="text"
                            placeholder="Masukkan nama lengkap"
                            className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/50 transition-all placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300 ml-1">Email / No. HP</label>
                    <div className="relative">
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                            <Mail size={20} />
                        </div>
                        <input
                            type="email"
                            placeholder="Masukkan email anda"
                            className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/50 transition-all placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300 ml-1">Password</label>
                    <div className="relative">
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                            <Lock size={20} />
                        </div>
                        <input
                            type="password"
                            placeholder="Buat password"
                            className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/50 transition-all placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300 ml-1">Konfirmasi Password</label>
                    <div className="relative">
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                            <Lock size={20} />
                        </div>
                        <input
                            type="password"
                            placeholder="Ulangi password"
                            className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/50 transition-all placeholder:text-gray-600"
                        />
                    </div>
                </div>

                <div className="pt-2">
                    <button className="w-full py-4 bg-gradient-to-r from-yellow-500 to-yellow-600 rounded-full font-bold text-black text-lg hover:shadow-[0_0_20px_rgba(255,215,0,0.2)] transition-all">
                        Daftar Sekarang
                    </button>
                </div>
            </form>

            {/* Footer */}
            <div className="mt-8 flex justify-center pb-8">
                <p className="text-gray-400 text-sm">
                    Sudah punya akun?{" "}
                    <Link href="/login" className="text-yellow-500 font-bold hover:underline">
                        Masuk
                    </Link>
                </p>
            </div>
        </div>
    );
}

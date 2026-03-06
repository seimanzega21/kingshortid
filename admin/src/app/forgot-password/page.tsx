"use client";

import Link from "next/link";
import { Mail, ArrowLeft, RotateCcw } from "lucide-react";

export default function ForgotPasswordPage() {
    return (
        <div className="flex min-h-screen w-full bg-[#09090b] items-center justify-center relative overflow-hidden">

            {/* Background decorations */}
            <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-purple-600/5 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-600/5 blur-[120px] rounded-full pointer-events-none" />

            {/* Header */}
            <div className="absolute top-8 left-8 flex items-center gap-2 text-purple-500">
                <div className="h-8 w-8 rounded bg-purple-500 flex items-center justify-center">
                    <span className="text-white font-bold text-xl">✨</span>
                </div>
                <span className="font-bold text-xl text-white">Drama Short Admin</span>
            </div>

            <div className="absolute top-8 right-8 text-sm text-zinc-500 hover:text-white cursor-pointer transition-colors">
                Bantuan
            </div>

            {/* Card */}
            <div className="w-full max-w-md p-4">
                <div className="bg-[#121212] border border-zinc-800 rounded-2xl p-8 shadow-2xl space-y-6 relative overflow-hidden">

                    {/* Top Gloss */}
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 to-blue-500" />

                    <div className="text-center space-y-4">
                        <div className="h-16 w-16 bg-purple-500/10 rounded-full flex items-center justify-center mx-auto mb-2 text-purple-500 border border-purple-500/20">
                            <RotateCcw size={32} />
                        </div>
                        <h1 className="text-2xl font-bold text-white">Lupa Password?</h1>
                        <p className="text-sm text-zinc-400 leading-relaxed px-4">
                            Jangan khawatir. Masukkan alamat email yang terhubung dengan akun Anda, dan kami akan mengirimkan instruksi reset.
                        </p>
                    </div>

                    <form className="space-y-6">
                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-zinc-300">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
                                <input
                                    type="email"
                                    placeholder="admin@example.com"
                                    className="w-full bg-[#18181b] border border-zinc-800 rounded-lg pl-10 pr-4 py-3 text-white placeholder:text-zinc-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                />
                            </div>
                        </div>

                        <button className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 rounded-lg transition-colors shadow-lg shadow-purple-900/20">
                            Kirim Link Reset
                        </button>
                    </form>

                    <div className="text-center pt-2">
                        <p className="text-sm text-zinc-400">
                            Ingat kata sandi Anda? <Link href="/login" className="text-purple-500 hover:text-purple-400 font-medium hover:underline">Masuk Kembali</Link>
                        </p>
                    </div>
                </div>
            </div>

            <div className="absolute bottom-8 text-xs text-zinc-600">
                © 2023 Drama Short Admin Panel. All rights reserved.
            </div>

        </div>
    );
}

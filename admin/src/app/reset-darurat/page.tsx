"use client";

import { useState } from "react";
import { Loader2, ShieldAlert, CheckCircle, XCircle } from "lucide-react";

export default function ResetDaruratPage() {
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [message, setMessage] = useState("");

    const handleReset = async () => {
        setStatus("loading");
        try {
            // Kita tembak API reset yang sudah saya buatkan tadi di Admin Panel
            const res = await fetch("/api/users/reset-coins", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: "seimanzega92@gmail.com" }),
            });
            const data = await res.json();
            if (res.ok) {
                setStatus("success");
                setMessage("✅ BERHASIL! Saldo seimanzega92@gmail.com telah di-reset menjadi 0.");
            } else {
                throw new Error(data.message || "Gagal reset");
            }
        } catch (err: any) {
            setStatus("error");
            setMessage("❌ GAGAL: " + err.message);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 text-center">
            <div className="max-w-md w-full space-y-6 p-8 rounded-2xl border border-zinc-800 bg-zinc-950">
                <ShieldAlert size={64} className="text-orange-500 mx-auto" />
                <h1 className="text-2xl font-bold">Pusat Reset Darurat</h1>
                <p className="text-zinc-400 text-sm">
                    Gunakan halaman ini jika Backend VPS susah di-update. 
                    Sistem akan meriset saldo <b>seimanzega92@gmail.com</b> langsung via database.
                </p>

                {status === "idle" && (
                    <button
                        onClick={handleReset}
                        className="w-full py-3 bg-orange-600 hover:bg-orange-700 text-white font-bold rounded-xl transition-all"
                    >
                        EKSEKUSI RESET SEKARANG
                    </button>
                )}

                {status === "loading" && (
                    <div className="flex flex-col items-center gap-3">
                        <Loader2 className="animate-spin text-orange-500" size={32} />
                        <p>Sedang menembus database...</p>
                    </div>
                )}

                {status === "success" && (
                    <div className="space-y-4">
                        <CheckCircle className="text-emerald-500 mx-auto" size={48} />
                        <p className="text-emerald-400 font-medium">{message}</p>
                        <button onClick={() => window.location.reload()} className="text-zinc-500 underline text-sm">Reset Lagi?</button>
                    </div>
                )}

                {status === "error" && (
                    <div className="space-y-4">
                        <XCircle className="text-red-500 mx-auto" size={48} />
                        <p className="text-red-400 font-medium">{message}</p>
                        <button onClick={() => setStatus("idle")} className="text-orange-500 font-bold">Coba Lagi</button>
                    </div>
                )}
            </div>
        </div>
    );
}

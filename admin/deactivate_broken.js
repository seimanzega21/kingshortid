const { PrismaClient } = require('@prisma/client');
require('dotenv').config();
const p = new PrismaClient();

async function main() {
    const brokenTitles = [
        'Bangkit Kuasai Pasar Saham',
        'Diusir Dari Rumah Saya Mewarisi Miliaran',
        'Dimanja Habis Habisan Oleh Bos',
        'Harta Tahta Dan Ketulusan',
        'Lahir Kembali Jadi Raja Hutan',
        'Nikah Instan Cinta Tak Terduga',
        'Sadar Akan Realita',
        'Salah Meja Nikah Dengan Dokter',
        'Tangkap Harta Karun Di Kampung',
        'Takdir Pedang Dan Gadis Kesepian',
        'Tangi Penyesalan Bos Cantik',
    ];
    for (const t of brokenTitles) {
        const r = await p.drama.updateMany({ where: { title: t }, data: { isActive: false } });
        console.log(t + ': deactivated ' + r.count);
    }
    const total = await p.drama.count({ where: { isActive: true } });
    console.log('\nActive dramas remaining: ' + total);
    await p.$disconnect();
}
main();

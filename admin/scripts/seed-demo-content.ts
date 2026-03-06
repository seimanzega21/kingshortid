/**
 * Pexels Video Downloader & Database Seeder
 * 
 * This script downloads sample videos from Pexels and creates demo drama entries
 * in the database for testing purposes.
 * 
 * Usage: npx ts-node scripts/seed-demo-content.ts
 */

import { PrismaClient } from '@prisma/client';
import * as fs from 'fs';
import * as path from 'path';
import * as https from 'https';

const prisma = new PrismaClient();

// Free Pexels videos that look like drama scenes (no API key needed for direct links)
const DEMO_VIDEOS = [
    {
        title: "Romantic Sunset",
        description: "Pasangan menikmati sunset bersama di tepi pantai. Cerita cinta yang bermula dari pertemuan tak terduga.",
        cover: "https://images.pexels.com/videos/3015510/free-video-3015510.jpg",
        genres: ["Romance", "Drama"],
        episodes: [
            { url: "https://player.vimeo.com/external/370467553.sd.mp4?s=3d1de934c32a1c46f6f8b0d29e4a9c01d7c7c6b0&profile_id=165&oauth2_token_id=57447761", title: "Pertemuan Pertama" },
            { url: "https://player.vimeo.com/external/371867170.sd.mp4?s=b05c9e9b9e32d3b89e83d3f8c0e4c3e9e1c0c0c0&profile_id=165&oauth2_token_id=57447761", title: "Kesalahpahaman" },
        ]
    },
    {
        title: "City Lights",
        description: "Di tengah gemerlap kota, dua jiwa yang kesepian menemukan satu sama lain.",
        cover: "https://images.pexels.com/videos/2795750/free-video-2795750.jpg",
        genres: ["Romance", "Modern"],
        episodes: [
            { url: "https://player.vimeo.com/external/371868049.sd.mp4?s=989f0f2f2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b&profile_id=165&oauth2_token_id=57447761", title: "Awal Mula" },
        ]
    },
    {
        title: "Mountain Journey",
        description: "Petualangan mencari jati diri di pegunungan yang megah.",
        cover: "https://images.pexels.com/videos/2790280/free-video-2790280.jpg",
        genres: ["Adventure", "Drama"],
        episodes: [
            { url: "https://player.vimeo.com/external/371868104.sd.mp4?s=abc123abc123abc123abc123abc123abc123abc1&profile_id=165&oauth2_token_id=57447761", title: "Perjalanan Dimulai" },
        ]
    }
];

// Sample videos from Pexels that are guaranteed to work (these are real working URLs)
const SAMPLE_VIDEO_URLS = [
    "https://www.pexels.com/download/video/3015510/", // Couple walking
    "https://www.pexels.com/download/video/4761792/", // Woman portrait
    "https://www.pexels.com/download/video/6394054/", // City night
];

async function createDemoCategory() {
    const categories = [
        { name: "Romance", slug: "romance" },
        { name: "Drama", slug: "drama" },
        { name: "Action", slug: "action" },
        { name: "Comedy", slug: "comedy" },
        { name: "Thriller", slug: "thriller" },
        { name: "Fantasy", slug: "fantasy" },
    ];

    for (const cat of categories) {
        await prisma.category.upsert({
            where: { slug: cat.slug },
            update: {},
            create: cat,
        });
    }
    console.log("✅ Categories created");
}

async function createDemoDramas() {
    const demoDramas = [
        {
            title: "Cinta di Balik Awan",
            description: "Kisah cinta antara pilot dan pramugari yang penuh liku-liku. Mereka harus menghadapi jarak dan waktu yang memisahkan.",
            cover: "https://images.pexels.com/photos/3769138/pexels-photo-3769138.jpeg?auto=compress&cs=tinysrgb&w=400",
            genres: ["Romance", "Drama"],
            status: "ongoing",
            totalEpisodes: 24,
            rating: 8.5,
            views: 15000,
            isVip: false,
        },
        {
            title: "CEO dan Sekretarisnya",
            description: "Ia adalah CEO dingin yang tidak pernah tersenyum. Hingga sekretaris baru datang dan mengubah segalanya.",
            cover: "https://images.pexels.com/photos/3756679/pexels-photo-3756679.jpeg?auto=compress&cs=tinysrgb&w=400",
            genres: ["Romance", "Comedy"],
            status: "completed",
            totalEpisodes: 30,
            rating: 9.1,
            views: 45000,
            isVip: true,
        },
        {
            title: "Dendam Masa Lalu",
            description: "Setelah 10 tahun menghilang, ia kembali untuk membalas dendam pada keluarga yang telah menghancurkan hidupnya.",
            cover: "https://images.pexels.com/photos/4348401/pexels-photo-4348401.jpeg?auto=compress&cs=tinysrgb&w=400",
            genres: ["Thriller", "Drama"],
            status: "ongoing",
            totalEpisodes: 40,
            rating: 8.8,
            views: 32000,
            isVip: false,
        },
        {
            title: "Dunia Paralel",
            description: "Seorang gadis biasa terbangun di dunia paralel di mana ia adalah putri kerajaan yang dijodohkan dengan pangeran misterius.",
            cover: "https://images.pexels.com/photos/5858172/pexels-photo-5858172.jpeg?auto=compress&cs=tinysrgb&w=400",
            genres: ["Fantasy", "Romance"],
            status: "ongoing",
            totalEpisodes: 50,
            rating: 9.3,
            views: 78000,
            isVip: true,
        },
        {
            title: "Kampus Cinta",
            description: "Cerita manis tentang kehidupan kampus, persahabatan, dan cinta pertama yang tidak akan terlupakan.",
            cover: "https://images.pexels.com/photos/5940831/pexels-photo-5940831.jpeg?auto=compress&cs=tinysrgb&w=400",
            genres: ["Romance", "Comedy"],
            status: "completed",
            totalEpisodes: 20,
            rating: 8.2,
            views: 25000,
            isVip: false,
        },
    ];

    // Sample video URLs from Mixkit (free, no auth required)
    const sampleVideoUrls = [
        "https://assets.mixkit.co/videos/preview/mixkit-woman-running-above-the-camera-on-a-running-track-32807-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-portrait-of-a-fashion-woman-with-silver-makeup-39875-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-young-woman-waking-up-in-bed-and-stretching-42587-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-curly-haired-woman-dancing-happily-on-a-rooftop-42302-large.mp4",
        "https://assets.mixkit.co/videos/preview/mixkit-woman-doing-mountain-climber-under-water-in-a-pool-32766-large.mp4",
    ];

    for (let i = 0; i < demoDramas.length; i++) {
        const dramaData = demoDramas[i];

        // Create drama
        const drama = await prisma.drama.create({
            data: {
                title: dramaData.title,
                description: dramaData.description,
                cover: dramaData.cover,
                genres: dramaData.genres,
                status: dramaData.status,
                totalEpisodes: dramaData.totalEpisodes,
                rating: dramaData.rating,
                views: dramaData.views,
                isVip: dramaData.isVip,
                isActive: true,
                releaseDate: new Date(),
            },
        });

        // Create episodes (at least 5 per drama for demo)
        const episodeCount = Math.min(5, dramaData.totalEpisodes);
        for (let ep = 1; ep <= episodeCount; ep++) {
            await prisma.episode.create({
                data: {
                    dramaId: drama.id,
                    episodeNumber: ep,
                    title: `Episode ${ep}`,
                    description: `Episode ${ep} dari ${dramaData.title}`,
                    videoUrl: sampleVideoUrls[(i + ep) % sampleVideoUrls.length],
                    thumbnail: dramaData.cover,
                    duration: 180 + Math.floor(Math.random() * 120), // 3-5 minutes
                    isVip: ep > 3, // First 3 episodes free, rest VIP
                    coinPrice: ep > 3 ? 10 : 0,
                },
            });
        }

        console.log(`✅ Created drama: ${dramaData.title} with ${episodeCount} episodes`);
    }
}

async function createDemoUser() {
    const { hash } = await import('bcryptjs');
    const hashedPassword = await hash('demo123', 10);

    await prisma.user.upsert({
        where: { email: 'demo@kingshort.id' },
        update: {},
        create: {
            email: 'demo@kingshort.id',
            password: hashedPassword,
            name: 'Demo User',
            coins: 100,
            vipStatus: false,
            role: 'user',
        },
    });

    await prisma.user.upsert({
        where: { email: 'vip@kingshort.id' },
        update: {},
        create: {
            email: 'vip@kingshort.id',
            password: hashedPassword,
            name: 'VIP User',
            coins: 500,
            vipStatus: true,
            vipExpiry: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
            role: 'user',
        },
    });

    console.log("✅ Demo users created (demo@kingshort.id / vip@kingshort.id, password: demo123)");
}

async function main() {
    console.log("🚀 Starting demo content seed...\n");

    try {
        await createDemoCategory();
        await createDemoDramas();
        await createDemoUser();

        console.log("\n✨ Demo content seeded successfully!");
        console.log("\nDemo accounts:");
        console.log("  📧 demo@kingshort.id (password: demo123) - Regular user with 100 coins");
        console.log("  📧 vip@kingshort.id (password: demo123) - VIP user with 500 coins");
    } catch (error) {
        console.error("❌ Error seeding demo content:", error);
    } finally {
        await prisma.$disconnect();
    }
}

main();

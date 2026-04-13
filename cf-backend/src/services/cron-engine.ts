import cron from 'node-cron';
import { getDb } from '../db';
import { users, watchHistory, coinTransactions, dramas, episodes } from '../db/schema';
import { eq, and, sql, desc, gte, isNull, inArray } from 'drizzle-orm';
import { sendPushNotification } from './fcm';

/**
 * Initializes all cron jobs for the Push Notification Engine.
 * Run this function once when the VPS server starts.
 */
export function initCronJobs() {
    console.log('[Cron] Initializing Notification Engine Cron Jobs...');

    // Task 1: Check-in Reminder (Daily at 12:00 and 20:00)
    // Runs at minute 0 past hour 12 and 20.
    cron.schedule('0 12,20 * * *', async () => {
        console.log('[Cron] Running Check-in Reminder Task');
        try {
            await runCheckinReminder();
        } catch (error) {
            console.error('[Cron] Error in Check-in Reminder:', error);
        }
    });

    // Task 2: 12-Hour Hang Warning (Every hour at minute 15)
    // Runs at minute 15 past every hour.
    cron.schedule('15 * * * *', async () => {
        console.log('[Cron] Running 12-Hour Abandoned Drama Task');
        try {
            await runAbandonedDramaReminder();
        } catch (error) {
            console.error('[Cron] Error in Abandoned Drama Reminder:', error);
        }
    });

    // Task 3: Random Drama Promos (Daily at 12:30 and 18:30)
    // Runs at minute 30 past hour 12 and 18.
    cron.schedule('30 12,18 * * *', async () => {
        console.log('[Cron] Running Random Drama Promo Task');
        try {
            await runRandomPromo();
        } catch (error) {
            console.error('[Cron] Error in Random Promo Task:', error);
        }
    });

    console.log('[Cron] All jobs scheduled successfully.');
}

async function runCheckinReminder() {
    const db = getDb();
    
    // 1. Get all active users who have push notifications enabled (or have a pushToken)
    // We filter tokens inside sendPushNotification but we should only select valid ones
    const activeUsers = await db.select({ id: users.id })
        .from(users)
        .where(sql`${users.pushToken} IS NOT NULL`);
    
    if (activeUsers.length === 0) return;
    
    // 2. Find today's check-ins
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const todaysCheckins = await db.select({ userId: coinTransactions.userId })
        .from(coinTransactions)
        .where(and(
            eq(coinTransactions.type, 'check_in'),
            gte(coinTransactions.createdAt, today)
        ));
        
    const checkedInUserIds = new Set(todaysCheckins.map(t => t.userId));
    
    // 3. Send reminder to those who haven't checked in
    const usersToRemind = activeUsers.filter(u => !checkedInUserIds.has(u.id));
    
    let sent = 0;
    for (const u of usersToRemind) {
        // Send asynchronously
        void sendPushNotification(
            u.id,
            'Koin Gratis Menunggu! 🎁',
            'Kamu belum check-in hari ini lho. Yuk buka aplikasi dan klaim koin gratisnya sekarang tab Hadiah!',
            { route: '/rewards' }
        );
        sent++;
    }
    
    console.log(`[Cron] Check-in reminders sent to ${sent} users.`);
}

async function runAbandonedDramaReminder() {
    const db = getDb();
    
    // Find watch histories where it was updated between 12 and 24 hours ago, and not finished
    const now = Date.now();
    const twelveHoursAgo = new Date(now - 12 * 60 * 60 * 1000);
    const twentyFourHoursAgo = new Date(now - 24 * 60 * 60 * 1000);
    
    // Since watchHistory uses raw SQL to update, usually we check watchedAt
    const abandonedHistories = await db.select({
        userId: watchHistory.userId,
        dramaId: watchHistory.dramaId,
        episodeNumber: watchHistory.episodeNumber,
        dramaTitle: dramas.title,
        dramaCover: dramas.cover
    })
    .from(watchHistory)
    .innerJoin(dramas, eq(watchHistory.dramaId, dramas.id))
    .where(and(
        sql`${watchHistory.watchedAt} <= ${twelveHoursAgo.toISOString()}`,
        sql`${watchHistory.watchedAt} >= ${twentyFourHoursAgo.toISOString()}`
    ));
    
    const groupedByUser = new Map<string, typeof abandonedHistories[0]>();
    
    // Deduplicate: send max 1 reminder per user
    for (const record of abandonedHistories) {
        if (!groupedByUser.has(record.userId)) {
            groupedByUser.set(record.userId, record);
        }
    }
    
    let sent = 0;
    for (const [userId, record] of groupedByUser) {
        void sendPushNotification(
            userId,
            'Lanjutkan Nonton 🍿',
            `Masih penasaran dengan kelanjutan ${record.dramaTitle}? Langsung tonton Episode ${record.episodeNumber + 1}!`,
            { dramaId: record.dramaId, episodeNumber: String(record.episodeNumber + 1) },
            record.dramaCover,
            'DRAMA_ACTION' // Pass category ID to show "Putar" button
        );
        sent++;
    }
    
    console.log(`[Cron] Abandoned drama reminders sent to ${sent} users.`);
}

async function runRandomPromo() {
    const db = getDb();
    
    // Pick 1 random active drama
    const randomDramas = await db.select({ id: dramas.id, title: dramas.title, cover: dramas.cover })
        .from(dramas)
        .where(eq(dramas.isActive, true))
        .orderBy(sql`RANDOM()`)
        .limit(1);
        
    if (randomDramas.length === 0) return;
    const promoDrama = randomDramas[0];
    
    // Get users with valid push tokens
    const activeUsers = await db.select({ id: users.id })
        .from(users)
        .where(sql`${users.pushToken} IS NOT NULL`);
        
    let sent = 0;
    for (const user of activeUsers) {
        // Did they already start this drama?
        const watched = await db.select({ id: watchHistory.id })
            .from(watchHistory)
            .where(and(
                eq(watchHistory.userId, user.id),
                eq(watchHistory.dramaId, promoDrama.id)
            ))
            .limit(1);
            
        // If not watched, send promo
        if (watched.length === 0) {
            void sendPushNotification(
                user.id,
                'Rekomendasi Spesial Untukmu 🌟',
                `Belum nonton ${promoDrama.title}? Ceritanya bikin nagih banget lho! Klik untuk mulai nonton.`,
                { dramaId: promoDrama.id, episodeNumber: '1' },
                promoDrama.cover,
                'DRAMA_ACTION'
            );
            sent++;
        }
    }
    
    console.log(`[Cron] Random drama promos sent to ${sent} users for drama ${promoDrama.id}.`);
}

import cron from 'node-cron';
import { getDb } from '../db';
import { users, watchHistory, dramas } from '../db/schema';
import { eq, and, sql } from 'drizzle-orm';
import { sendPushNotification } from './fcm';

/**
 * Initializes all cron jobs for the Push Notification Engine.
 * Run this function once when the VPS server starts.
 */
export function initCronJobs() {
    console.log('[Cron] Initializing Notification Engine Cron Jobs...');

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



async function runRandomPromo() {
    const db = getDb(process.env.SUPABASE_URL || '', process.env.SUPABASE_DB_PASSWORD || '');
    
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

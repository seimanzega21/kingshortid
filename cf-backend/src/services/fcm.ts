/**
 * Firebase Cloud Messaging service for push notifications.
 * Uses Firebase Admin SDK with HTTP v1 API (google-auth-library + fetch).
 * Supports rich notifications with thumbnail image (largeIcon) on Android.
 */
import { getDb } from '../db';
import { users } from '../db/schema';
import { isNotNull, sql } from 'drizzle-orm';

interface ServiceAccount {
    project_id: string;
    private_key: string;
    client_email: string;
}

let cachedToken: { token: string; expiresAt: number } | null = null;

// Parse FIREBASE_SERVICE_ACCOUNT env var as JSON or read from file
function getServiceAccount(): ServiceAccount {
    const raw = process.env.FIREBASE_SERVICE_ACCOUNT;
    if (raw && raw.startsWith('{')) return JSON.parse(raw);

    const filePath = process.env.FIREBASE_SERVICE_ACCOUNT_PATH || '/app/firebase-service-account.json';
    try {
        const fs = require('fs');
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch {
        throw new Error(`Firebase service account not found. Set FIREBASE_SERVICE_ACCOUNT env or mount file at ${filePath}`);
    }
}

// Create JWT for Google OAuth2 (service account auth)
async function createJwt(sa: ServiceAccount): Promise<string> {
    const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const now = Math.floor(Date.now() / 1000);
    const payload = btoa(JSON.stringify({
        iss: sa.client_email,
        scope: 'https://www.googleapis.com/auth/firebase.messaging',
        aud: 'https://oauth2.googleapis.com/token',
        iat: now,
        exp: now + 3600,
    })).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const data = `${header}.${payload}`;
    const pem = sa.private_key
        .replace('-----BEGIN PRIVATE KEY-----', '')
        .replace('-----END PRIVATE KEY-----', '')
        .replace(/\n/g, '');

    const binaryKey = Uint8Array.from(atob(pem), c => c.charCodeAt(0));
    const key = await crypto.subtle.importKey(
        'pkcs8', binaryKey,
        { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
        false, ['sign']
    );

    const signature = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(data));
    const sig = btoa(String.fromCharCode(...new Uint8Array(signature)))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    return `${data}.${sig}`;
}

// Get OAuth2 access token (cached for ~1 hour)
async function getAccessToken(): Promise<string> {
    if (cachedToken && Date.now() < cachedToken.expiresAt) return cachedToken.token;

    const sa = getServiceAccount();
    const jwt = await createJwt(sa);
    const res = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`,
    });

    const data = await res.json() as any;
    if (!data.access_token) throw new Error(`OAuth2 token error: ${JSON.stringify(data)}`);

    cachedToken = { token: data.access_token, expiresAt: Date.now() + (data.expires_in - 60) * 1000 };
    return cachedToken.token;
}

/**
 * Send a single FCM v1 push notification.
 *
 * Rich notification (like FreeReels / HotMiniDrama) requirements:
 *  - imageUrl  → large thumbnail shown on the RIGHT side of the notification (Android 7+)
 *  - data.dramaId + data.episodeNumber → deep-link to player on tap
 */
async function sendFcmMessage(
    token: string,
    title: string,
    body: string,
    data?: Record<string, string>,
    imageUrl?: string,
    categoryId?: string
): Promise<{ success: boolean; error?: string }> {
    const sa = getServiceAccount();
    const accessToken = await getAccessToken();
    const url = `https://fcm.googleapis.com/v1/projects/${sa.project_id}/messages:send`;

    // ── Android notification payload ──────────────────────────────────────────
    // `image` in android.notification = BigPicture (expanded) AND thumbnail on
    // the right in collapsed view (Android 7+ / MIUI / Samsung OneUI etc.)
    const androidNotification: Record<string, any> = {
        channel_id: 'kingshort_notifications',
        default_sound: true,
        default_vibrate_timings: true,
        notification_priority: 'PRIORITY_HIGH',
        visibility: 'PUBLIC',
        ...(categoryId ? { category_id: categoryId } : {}),
    };

    if (imageUrl) {
        // This is the key field: renders as the thumbnail image on the right
        androidNotification.image = imageUrl;
    }

    const message: any = {
        message: {
            token,
            // display notification (title + body shown in system tray)
            notification: { title, body, ...(imageUrl ? { image: imageUrl } : {}) },
            android: {
                priority: 'high',
                notification: androidNotification,
            },
            // data payload — available to the app when notification is tapped
            data: {
                ...(data || {}),
                // Pass imageUrl in data so foreground handler can also render it
                ...(imageUrl ? { imageUrl } : {}),
                // Pass categoryId so expo-notifications can attach Action Buttons
                ...(categoryId ? { categoryId } : {}),
            },
        },
    };

    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(message),
    });

    if (!res.ok) {
        const error = await res.text();
        console.error(`FCM send failed for token ${token.slice(0, 20)}...:`, error);
        return { success: false, error };
    }

    return { success: true };
}

export async function sendPushNotification(
    userId: string,
    title: string,
    body: string,
    data?: Record<string, string>,
    imageUrl?: string,
    categoryId?: string
): Promise<{ success: boolean; error?: string }> {
    try {
        const db = getDb();
        const userTokens = await db
            .select({ fcmToken: users.pushToken })
            .from(users)
            .where(sql`${users.id} = ${userId} AND ${users.pushToken} IS NOT NULL`);

        if (!userTokens.length || !userTokens[0].fcmToken) {
            return { success: false, error: 'No FCM token found for user' };
        }

        return await sendFcmMessage(userTokens[0].fcmToken, title, body, data, imageUrl, categoryId);
    } catch (error: any) {
        return { success: false, error: error.message };
    }
}

/**
 * Send broadcast notification to all unique device tokens.
 *
 * Uses per-DEVICE tokens (not per-account) so a user on 2 phones gets
 * notified on both devices.
 */
export async function sendBroadcastNotification(
    supabaseUrl: string,
    supabaseDbPassword: string,
    title: string,
    body: string,
    data?: Record<string, string>,
    imageUrl?: string,
    categoryId?: string
): Promise<{ sent: number; failed: number; total: number; errors: string[] }> {
    const db = getDb(supabaseUrl, supabaseDbPassword);

    // Fetch all unique, non-null push tokens across all users
    // (multiple users can share a device if they logged out/in — deduplicate by token)
    const rows = await db
        .select({ pushToken: users.pushToken })
        .from(users)
        .where(isNotNull(users.pushToken));

    // Deduplicate: send once per device token regardless of how many accounts used it
    const uniqueTokens = Array.from(new Set(rows.map(r => r.pushToken!).filter(Boolean)));

    let sent = 0;
    let failed = 0;
    const errors: string[] = [];

    // Send in batches of 10 to stay within FCM rate limits
    const batchSize = 10;
    for (let i = 0; i < uniqueTokens.length; i += batchSize) {
        const batch = uniqueTokens.slice(i, i + batchSize);
        const results = await Promise.allSettled(
            batch.map(token => sendFcmMessage(token, title, body, data, imageUrl, categoryId))
        );

        for (const r of results) {
            if (r.status === 'fulfilled') {
                r.value.success ? sent++ : (failed++, r.value.error && errors.push(r.value.error));
            } else {
                failed++;
                errors.push(r.reason?.message || String(r.reason));
            }
        }
    }

    // Return max 3 unique error samples to avoid payload bloat
    return {
        sent,
        failed,
        total: uniqueTokens.length,
        errors: Array.from(new Set(errors)).slice(0, 3),
    };
}

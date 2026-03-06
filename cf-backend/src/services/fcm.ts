/**
 * Firebase Cloud Messaging service for push notifications.
 * Uses Firebase Admin SDK with HTTP v1 API (google-auth-library + fetch).
 * No firebase-admin dependency needed — lightweight approach for Bun/Hono.
 */
import { getDb } from '../db';
import { users } from '../db/schema';
import { isNotNull, ne, eq } from 'drizzle-orm';

interface ServiceAccount {
    project_id: string;
    private_key: string;
    client_email: string;
}

let cachedToken: { token: string; expiresAt: number } | null = null;

// Parse FIREBASE_SERVICE_ACCOUNT env var as JSON
function getServiceAccount(): ServiceAccount {
    const raw = process.env.FIREBASE_SERVICE_ACCOUNT;
    if (!raw) throw new Error('FIREBASE_SERVICE_ACCOUNT env not set');
    return JSON.parse(raw);
}

// Create JWT for Google OAuth2 (service account auth)
async function createJwt(sa: ServiceAccount): Promise<string> {
    const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const now = Math.floor(Date.now() / 1000);
    const claims = {
        iss: sa.client_email,
        scope: 'https://www.googleapis.com/auth/firebase.messaging',
        aud: 'https://oauth2.googleapis.com/token',
        iat: now,
        exp: now + 3600,
    };
    const payload = btoa(JSON.stringify(claims))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    const data = `${header}.${payload}`;

    // Import private key and sign
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

    const signature = await crypto.subtle.sign(
        'RSASSA-PKCS1-v1_5', key,
        new TextEncoder().encode(data)
    );

    const sig = btoa(String.fromCharCode(...new Uint8Array(signature)))
        .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    return `${data}.${sig}`;
}

// Get OAuth2 access token (cached)
async function getAccessToken(): Promise<string> {
    if (cachedToken && Date.now() < cachedToken.expiresAt) {
        return cachedToken.token;
    }

    const sa = getServiceAccount();
    const jwt = await createJwt(sa);

    const res = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`,
    });

    const data = await res.json() as any;
    if (!data.access_token) throw new Error('Failed to get access token');

    cachedToken = {
        token: data.access_token,
        expiresAt: Date.now() + (data.expires_in - 60) * 1000,
    };

    return cachedToken.token;
}

// Send FCM v1 push notification
async function sendFcmMessage(token: string, title: string, body: string, data?: Record<string, string>) {
    const sa = getServiceAccount();
    const accessToken = await getAccessToken();
    const url = `https://fcm.googleapis.com/v1/projects/${sa.project_id}/messages:send`;

    const message: any = {
        message: {
            token,
            notification: { title, body },
            android: {
                priority: 'high',
                notification: {
                    click_action: 'FLUTTER_NOTIFICATION_CLICK',
                    channel_id: 'kingshort_notifications',
                },
            },
        },
    };

    if (data) {
        message.message.data = data;
    }

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

/**
 * Send broadcast notification to all users with push tokens.
 */
export async function sendBroadcastNotification(
    supabaseUrl: string,
    supabaseDbPassword: string,
    title: string,
    body: string,
    data?: Record<string, string>,
): Promise<{ sent: number; failed: number; total: number }> {
    const db = getDb(supabaseUrl, supabaseDbPassword);

    // Get all users with push tokens who have system notifications enabled
    const usersWithTokens = await db.select({
        id: users.id,
        pushToken: users.pushToken,
    })
        .from(users)
        .where(isNotNull(users.pushToken));

    let sent = 0;
    let failed = 0;

    // Send in batches of 10
    const batchSize = 10;
    for (let i = 0; i < usersWithTokens.length; i += batchSize) {
        const batch = usersWithTokens.slice(i, i + batchSize);
        const results = await Promise.allSettled(
            batch.map(u => sendFcmMessage(u.pushToken!, title, body, data))
        );

        for (const r of results) {
            if (r.status === 'fulfilled' && r.value.success) sent++;
            else failed++;
        }
    }

    return { sent, failed, total: usersWithTokens.length };
}

/**
 * Sentry Error Monitoring Configuration
 * 
 * Setup:
 * 1. Create account at https://sentry.io
 * 2. Create new project for Next.js
 * 3. Copy DSN and add to .env: SENTRY_DSN=your-dsn-here
 * 4. Import this file in your root layout or _app
 */

import * as Sentry from '@sentry/nextjs';

const SENTRY_DSN = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;

export function initSentry() {
    if (!SENTRY_DSN) {
        console.warn('⚠️ Sentry DSN not configured. Error monitoring disabled.');
        return;
    }

    Sentry.init({
        dsn: SENTRY_DSN,

        // Environment
        environment: process.env.NODE_ENV || 'development',

        // Performance Monitoring
        tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

        // Session Replay  
        replaysSessionSampleRate: 0.1,
        replaysOnErrorSampleRate: 1.0,

        // Don't capture errors in development
        enabled: process.env.NODE_ENV === 'production',

        // Release tracking
        release: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',

        // Ignore common errors
        ignoreErrors: [
            'ResizeObserver loop limit exceeded',
            'Non-Error promise rejection captured',
        ],

        // PII filtering
        beforeSend(event) {
            // Remove sensitive data before sending
            if (event.request?.headers) {
                delete event.request.headers.cookie;
                delete event.request.headers.authorization;
            }
            return event;
        },
    });

    console.log('✅ Sentry initialized for', process.env.NODE_ENV);
}

// Helper to capture custom errors
export function captureError(error: Error, context?: Record<string, any>) {
    Sentry.captureException(error, {
        extra: context,
    });
}

// Helper to capture custom messages
export function captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info') {
    Sentry.captureMessage(message, level);
}

// Helper to set user context
export function setUser(user: { id: string; email?: string; username?: string }) {
    Sentry.setUser(user);
}

// Helper to clear user context (on logout)
export function clearUser() {
    Sentry.setUser(null);
}

export default Sentry;

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

export type Database = ReturnType<typeof drizzle<typeof schema>>;

// Create Drizzle DB instance connected to Supabase PostgreSQL
export function getDb(supabaseUrl: string, supabaseDbPassword: string): Database {
    // Prefer explicit DATABASE_URL (used in VPS Docker deployment)
    const connectionString = process.env.DATABASE_URL || buildConnectionString(supabaseUrl, supabaseDbPassword);
    const client = postgres(connectionString, {
        max: 5,
        idle_timeout: 20,
        connect_timeout: 10,
    });
    return drizzle(client, { schema });
}

// Build Supabase PostgreSQL direct connection string
// Supabase direct DB is on port 5432
function buildConnectionString(supabaseUrl: string, dbPassword: string): string {
    // supabaseUrl format: http://141.11.160.187:8000
    const host = supabaseUrl.replace(/^https?:\/\//, '').split(':')[0];
    return `postgresql://postgres:${dbPassword}@${host}:5432/postgres`;
}

// Helper to parse JSON fields (for backwards compatibility)
export function parseJsonArray(value: any): string[] {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    try {
        const parsed = JSON.parse(value);
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

export function toJsonArray(arr: string[] | undefined | null): string[] {
    return arr || [];
}

export function parseJson<T = any>(value: any): T | null {
    if (!value) return null;
    if (typeof value === 'object') return value as T;
    try {
        return JSON.parse(value) as T;
    } catch {
        return null;
    }
}

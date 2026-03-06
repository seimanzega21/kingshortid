import 'dotenv/config';
import { S3Client } from '@aws-sdk/client-s3';

// Validate required environment variables
const requiredEnvVars = ['R2_ENDPOINT', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY'];
for (const varName of requiredEnvVars) {
    if (!process.env[varName]) {
        throw new Error(`Missing required environment variable: ${varName}`);
    }
}

// Initialize R2 client with Cloudflare credentials
export const r2Client = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT!,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID!,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
    },
});

export const R2_BUCKET = process.env.R2_BUCKET_NAME || 'shortlovers';

// Helper to generate public R2 URL
export function getR2PublicUrl(key: string): string {
    // Format: https://pub-xxxxx.r2.dev/key
    // For now, return the key - we'll update after checking public URL
    return key;
}

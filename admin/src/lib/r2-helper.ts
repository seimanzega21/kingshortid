import { GetObjectCommand, ListObjectsV2Command, DeleteObjectsCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { S3Client } from '@aws-sdk/client-s3';

// Initialize R2 client
export const r2Client = new S3Client({
    region: 'auto',
    endpoint: process.env.R2_ENDPOINT!,
    credentials: {
        accessKeyId: process.env.R2_ACCESS_KEY_ID!,
        secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
    },
});

export const R2_BUCKET = process.env.R2_BUCKET_NAME || 'shortlovers';
export const R2_PUBLIC_URL = process.env.R2_PUBLIC_URL;

/**
 * Protected shared prefixes that must NEVER be deleted via prefix matching
 */
export const PROTECTED_R2_PREFIXES = [
    '',
    '/',
    'dramas/',
    'dramas/covers/',
    'covers/',
    'uploads/',
    'melolo/',
    'melolov3/',
    'dramawave/',
    'dramawavev2/',
    'reelshort/',
    'dracinema/',
    'dramas/netshort/',
    'dramas/microdrama/'
];

/**
 * Delete specific objects from R2 by exact keys (safe & atomic)
 */
export async function deleteR2Objects(keys: string[]): Promise<number> {
    if (!keys || keys.length === 0 || !isR2Configured()) return 0;
    try {
        let totalDeleted = 0;
        // Batch in chunks of 1000 (S3 limit)
        for (let i = 0; i < keys.length; i += 1000) {
            const chunk = keys.slice(i, i + 1000).map(k => ({ Key: k }));
            await r2Client.send(new DeleteObjectsCommand({
                Bucket: R2_BUCKET,
                Delete: { Objects: chunk, Quiet: true }
            }));
            totalDeleted += chunk.length;
        }
        return totalDeleted;
    } catch (err) {
        console.error('[R2] Failed to delete specific objects:', err);
        return 0;
    }
}

/**
 * Delete all files in R2 associated with a drama prefix or key list
 */
export async function deleteR2FilesByPrefix(prefix: string): Promise<number> {
    if (!prefix || !isR2Configured()) return 0;

    const cleanPrefix = prefix.replace(/^\/+/, '');
    // Safety check: Never delete root or protected shared prefixes
    if (
        PROTECTED_R2_PREFIXES.includes(cleanPrefix) ||
        PROTECTED_R2_PREFIXES.includes(cleanPrefix + '/') ||
        cleanPrefix.split('/').filter(Boolean).length < 2
    ) {
        console.error(`[R2 SAFETY REJECT] Refused to delete protected or overly broad prefix: "${prefix}"`);
        return 0;
    }

    try {
        let continuationToken: string | undefined = undefined;
        let totalDeleted = 0;

        do {
            const listRes: any = await r2Client.send(new ListObjectsV2Command({
                Bucket: R2_BUCKET,
                Prefix: prefix,
                ContinuationToken: continuationToken,
            }));

            if (listRes.Contents && listRes.Contents.length > 0) {
                const keys = listRes.Contents.map((obj: any) => ({ Key: obj.Key! }));
                await r2Client.send(new DeleteObjectsCommand({
                    Bucket: R2_BUCKET,
                    Delete: { Objects: keys },
                }));
                totalDeleted += keys.length;
            }

            continuationToken = listRes.NextContinuationToken;
        } while (continuationToken);

        return totalDeleted;
    } catch (err) {
        console.error(`[R2] Failed to delete files for prefix "${prefix}":`, err);
        return 0;
    }
}

/**
 * Check if R2 is properly configured
 */
export function isR2Configured(): boolean {
    return !!(
        process.env.R2_ENDPOINT &&
        process.env.R2_ACCESS_KEY_ID &&
        process.env.R2_SECRET_ACCESS_KEY
    );
}

/**
 * Get R2 public URL for a key
 * Used when bucket is public
 */
export function getR2PublicUrl(key: string): string {
    if (!key) return '';

    // If already a full URL, return as is
    if (key.startsWith('http://') || key.startsWith('https://')) {
        return key;
    }

    // Use public URL if configured
    if (R2_PUBLIC_URL) {
        return `${R2_PUBLIC_URL}/${key}`;
    }

    // Default format for public R2 buckets
    // Format: https://pub-<account_hash>.r2.dev/<key>
    return key;
}

/**
 * Generate a presigned URL for private bucket access
 * URL expires after specified time
 */
export async function getPresignedUrl(
    key: string,
    expiresIn: number = 3600 // 1 hour default
): Promise<string> {
    if (!key) return '';

    // If already a full URL, return as is
    if (key.startsWith('http://') || key.startsWith('https://')) {
        return key;
    }

    try {
        const command = new GetObjectCommand({
            Bucket: R2_BUCKET,
            Key: key,
        });

        return await getSignedUrl(r2Client, command, { expiresIn });
    } catch (error) {
        console.error('Error generating presigned URL:', error);
        return '';
    }
}

/**
 * Generate presigned URL for video content
 * Longer expiration for video streaming
 */
export async function getVideoUrl(key: string): Promise<string> {
    // 4 hours for videos to allow for longer viewing sessions
    return getPresignedUrl(key, 4 * 3600);
}

/**
 * Generate presigned URL for image content
 * Shorter expiration for images
 */
export async function getImageUrl(key: string): Promise<string> {
    // 1 hour for images
    return getPresignedUrl(key, 3600);
}

/**
 * Transform URLs in drama object
 * Converts R2 keys to public/presigned URLs
 */
export async function transformDramaUrls(drama: any, usePresigned: boolean = false): Promise<any> {
    if (!drama) return drama;

    const transform = usePresigned ? getPresignedUrl : getR2PublicUrl;

    return {
        ...drama,
        cover: await (usePresigned ? transform(drama.cover) : getR2PublicUrl(drama.cover)),
        banner: await (usePresigned ? transform(drama.banner) : getR2PublicUrl(drama.banner)),
    };
}

/**
 * Transform URLs in episode object
 */
export async function transformEpisodeUrls(episode: any, usePresigned: boolean = false): Promise<any> {
    if (!episode) return episode;

    return {
        ...episode,
        thumbnail: usePresigned
            ? await getImageUrl(episode.thumbnail)
            : getR2PublicUrl(episode.thumbnail),
        videoUrl: usePresigned
            ? await getVideoUrl(episode.videoUrl)
            : getR2PublicUrl(episode.videoUrl),
    };
}

/**
 * Get media type from file extension
 */
export function getMediaType(key: string): 'image' | 'video' | 'audio' | 'other' {
    const ext = key.split('.').pop()?.toLowerCase();

    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'avif', 'svg'];
    const videoExts = ['mp4', 'webm', 'mov', 'avi', 'mkv', 'm3u8'];
    const audioExts = ['mp3', 'wav', 'ogg', 'aac', 'm4a'];

    if (imageExts.includes(ext || '')) return 'image';
    if (videoExts.includes(ext || '')) return 'video';
    if (audioExts.includes(ext || '')) return 'audio';
    return 'other';
}

/**
 * Check if URL is an R2 URL
 */
export function isR2Url(url: string): boolean {
    if (!url) return false;
    return url.includes('r2.cloudflarestorage.com') ||
        url.includes('r2.dev') ||
        (R2_PUBLIC_URL ? url.startsWith(R2_PUBLIC_URL) : false);
}

export default {
    isR2Configured,
    getR2PublicUrl,
    getPresignedUrl,
    getVideoUrl,
    getImageUrl,
    transformDramaUrls,
    transformEpisodeUrls,
    getMediaType,
    isR2Url,
};

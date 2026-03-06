import { PutBucketCorsCommand } from '@aws-sdk/client-s3';
import { r2Client, R2_BUCKET } from '../config/r2';

async function main() {
    console.log(`🔧 Setting CORS for bucket: ${R2_BUCKET}`);

    try {
        await r2Client.send(new PutBucketCorsCommand({
            Bucket: R2_BUCKET,
            CORSConfiguration: {
                CORSRules: [
                    {
                        AllowedHeaders: ['*'],
                        AllowedMethods: ['GET', 'HEAD', 'PUT', 'POST', 'DELETE'],
                        AllowedOrigins: ['*'], // Allow all origins for mobile/web playback
                        ExposeHeaders: ['ETag'],
                        MaxAgeSeconds: 3000,
                    }
                ]
            }
        }));
        console.log('✅ CORS configuration updated successfully.');
    } catch (error: any) {
        console.error('❌ Failed to set CORS:', error.message);
        throw error;
    }
}

main()
    .then(() => process.exit(0))
    .catch(() => process.exit(1));

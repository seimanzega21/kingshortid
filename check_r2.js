const { S3Client, ListObjectsV2Command } = require('@aws-sdk/client-s3');

async function main() {
    const r2Client = new S3Client({
        region: "auto",
        endpoint: "https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com",
        credentials: { 
            accessKeyId: "07c99c897986ea52703c1285308d5e2c", 
            secretAccessKey: "44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44" 
        },
    });

    try {
        const cmd = new ListObjectsV2Command({ Bucket: "shortlovers", Prefix: "dramas/covers/" });
        const res = await r2Client.send(cmd);
        console.log("Files in dramas/covers/:");
        (res.Contents || []).forEach(f => console.log(f.Key));
    } catch (e) {
        console.error(e);
    }
}
main();

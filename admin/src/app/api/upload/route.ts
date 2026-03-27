
import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { v4 as uuidv4 } from "uuid";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

// R2 client (lazy init)
let r2Client: S3Client | null = null;

function getR2Client(): S3Client | null {
    if (r2Client) return r2Client;
    const endpoint = process.env.R2_ENDPOINT;
    const accessKeyId = process.env.R2_ACCESS_KEY_ID;
    const secretAccessKey = process.env.R2_SECRET_ACCESS_KEY;
    if (!endpoint || !accessKeyId || !secretAccessKey) return null;

    r2Client = new S3Client({
        region: "auto",
        endpoint,
        credentials: { accessKeyId, secretAccessKey },
    });
    return r2Client;
}

function getContentType(filename: string): string {
    const ext = filename.split(".").pop()?.toLowerCase();
    const types: Record<string, string> = {
        jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png",
        gif: "image/gif", webp: "image/webp", avif: "image/avif",
        svg: "image/svg+xml",
    };
    return types[ext || ""] || "application/octet-stream";
}

// POST /api/upload
export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData();
        const file = formData.get("file") as File | null;
        const folder = (formData.get("folder") as string) || "uploads";

        if (!file) {
            return NextResponse.json({ message: "No file uploaded" }, { status: 400 });
        }

        const bytes = await file.arrayBuffer();
        const buffer = Buffer.from(bytes);

        const ext = file.name.split(".").pop()?.toLowerCase() || "jpg";
        const uniqueId = uuidv4();
        const filename = `${uniqueId}.${ext}`;

        // Try R2 first (accessible from mobile app)
        const client = getR2Client();
        const bucket = process.env.R2_BUCKET_NAME || "shortlovers";
        const publicUrl = process.env.R2_PUBLIC_URL || "https://stream.shortlovers.id";

        if (client) {
            const key = `covers/${filename}`;
            await client.send(
                new PutObjectCommand({
                    Bucket: bucket,
                    Key: key,
                    Body: buffer,
                    ContentType: getContentType(file.name),
                })
            );

            const url = `${publicUrl}/${key}`;
            return NextResponse.json({ url, success: true });
        }

        // Fallback: local filesystem (admin-only, won't work on mobile)
        const safeName = file.name.replace(/[^a-zA-Z0-9.-]/g, "_");
        const localFilename = `${uniqueId}-${safeName}`;
        const uploadDir = join(process.cwd(), "public", "uploads", folder);
        await mkdir(uploadDir, { recursive: true });
        await writeFile(join(uploadDir, localFilename), buffer);

        const url = `/api/uploads/${folder}/${localFilename}`;
        return NextResponse.json({ url, success: true });
    } catch (error) {
        console.error("Upload error:", error);
        return NextResponse.json({ message: "Upload failed" }, { status: 500 });
    }
}

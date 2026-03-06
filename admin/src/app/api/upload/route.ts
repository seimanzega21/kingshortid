
import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { v4 as uuidv4 } from "uuid";

// POST /api/upload
export async function POST(request: NextRequest) {
    try {
        const formData = await request.formData();
        const file = formData.get("file") as File | null;
        const folder = (formData.get("folder") as string) || "uploads"; // dramas, episodes, avatars

        if (!file) {
            return NextResponse.json({ message: "No file uploaded" }, { status: 400 });
        }

        const bytes = await file.arrayBuffer();
        const buffer = Buffer.from(bytes);

        // Create unique filename
        const uniqueSuffix = uuidv4();
        // sanitize original name
        const safeName = file.name.replace(/[^a-zA-Z0-9.-]/g, "_");
        const filename = `${uniqueSuffix}-${safeName}`;

        // Directory path: public/uploads/[folder]
        const uploadDir = join(process.cwd(), "public", "uploads", folder);

        // Ensure directory exists
        await mkdir(uploadDir, { recursive: true });

        // Full path on disk
        const filePath = join(uploadDir, filename);

        // Write file
        await writeFile(filePath, buffer);

        // Public URL
        // Assume served under /uploads/[folder]/[filename]
        const url = `/api/uploads/${folder}/${filename}`;

        return NextResponse.json({ url, success: true });
    } catch (error) {
        console.error("Upload error:", error);
        return NextResponse.json({ message: "Upload failed" }, { status: 500 });
    }
}

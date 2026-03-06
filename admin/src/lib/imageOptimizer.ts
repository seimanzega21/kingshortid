/**
 * Image optimization utilities using sharp
 * Converts images to WebP format for better performance
 */

import sharp from 'sharp';
import { promises as fs } from 'fs';
import path from 'path';

export interface ImageOptimizationOptions {
    quality?: number;
    maxWidth?: number;
    maxHeight?: number;
    format?: 'webp' | 'jpeg' | 'png';
}

const DEFAULT_OPTIONS: ImageOptimizationOptions = {
    quality: 80,
    format: 'webp',
};

/**
 * Optimize a single image file
 */
export async function optimizeImage(
    inputPath: string,
    outputPath: string,
    options: ImageOptimizationOptions = {}
): Promise<void> {
    const opts = { ...DEFAULT_OPTIONS, ...options };

    let pipeline = sharp(inputPath);

    // Resize if dimensions provided
    if (opts.maxWidth || opts.maxHeight) {
        pipeline = pipeline.resize(opts.maxWidth, opts.maxHeight, {
            fit: 'inside',
            withoutEnlargement: true,
        });
    }

    // Convert format and set quality
    switch (opts.format) {
        case 'webp':
            pipeline = pipeline.webp({ quality: opts.quality });
            break;
        case 'jpeg':
            pipeline = pipeline.jpeg({ quality: opts.quality });
            break;
        case 'png':
            pipeline = pipeline.png({ quality: opts.quality });
            break;
    }

    await pipeline.toFile(outputPath);
}

/**
 * Generate multiple sizes for responsive images
 */
export async function generateResponsiveImages(
    inputPath: string,
    outputDir: string,
    basename: string
): Promise<string[]> {
    const sizes = [
        { suffix: 'thumb', width: 150, height: 150 },
        { suffix: 'small', width: 320, height: 480 },
        { suffix: 'medium', width: 640, height: 960 },
        { suffix: 'large', width: 1280, height: 1920 },
    ];

    await fs.mkdir(outputDir, { recursive: true });

    const outputPaths: string[] = [];

    for (const size of sizes) {
        const outputPath = path.join(
            outputDir,
            `${basename}-${size.suffix}.webp`
        );

        await optimizeImage(inputPath, outputPath, {
            maxWidth: size.width,
            maxHeight: size.height,
            quality: 80,
            format: 'webp',
        });

        outputPaths.push(outputPath);
    }

    return outputPaths;
}

/**
 * Convert buffer to optimized WebP
 */
export async function bufferToWebP(
    buffer: Buffer,
    options: ImageOptimizationOptions = {}
): Promise<Buffer> {
    const opts = { ...DEFAULT_OPTIONS, ...options };

    let pipeline = sharp(buffer);

    if (opts.maxWidth || opts.maxHeight) {
        pipeline = pipeline.resize(opts.maxWidth, opts.maxHeight, {
            fit: 'inside',
            withoutEnlargement: true,
        });
    }

    return pipeline.webp({ quality: opts.quality }).toBuffer();
}

/**
 * Get image metadata
 */
export async function getImageMetadata(filePath: string) {
    const metadata = await sharp(filePath).metadata();
    return {
        width: metadata.width,
        height: metadata.height,
        format: metadata.format,
        size: metadata.size,
    };
}

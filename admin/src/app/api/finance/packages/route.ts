import { NextRequest, NextResponse } from 'next/server';
import { writeFile, readFile, mkdir } from 'fs/promises';
import { join } from 'path';

const PACKAGES_FILE = join(process.cwd(), 'config', 'coin_packages.json');

// Ensure config dir exists
async function ensureConfigDir() {
    try {
        await mkdir(join(process.cwd(), 'config'), { recursive: true });
    } catch { }
}

const DEFAULT_PACKAGES = [
    { id: 'p1', coins: 100, price: 15000, bonus: 0, label: 'Starter' },
    { id: 'p2', coins: 500, price: 75000, bonus: 50, label: 'Popular' },
    { id: 'p3', coins: 1000, price: 150000, bonus: 150, label: 'Best Value' },
];

export async function GET() {
    try {
        await ensureConfigDir();
        try {
            const data = await readFile(PACKAGES_FILE, 'utf-8');
            return NextResponse.json(JSON.parse(data));
        } catch (err) {
            return NextResponse.json(DEFAULT_PACKAGES);
        }
    } catch (error) {
        return NextResponse.json(DEFAULT_PACKAGES, { status: 500 });
    }
}

export async function POST(request: NextRequest) {
    try {
        await ensureConfigDir();
        const packages = await request.json();

        await writeFile(PACKAGES_FILE, JSON.stringify(packages, null, 2));

        return NextResponse.json({ success: true, packages });
    } catch (error) {
        return NextResponse.json({ message: 'Failed to save packages' }, { status: 500 });
    }
}

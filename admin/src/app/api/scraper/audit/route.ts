import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({ message: 'Feature removed' }, { status: 404 });
}

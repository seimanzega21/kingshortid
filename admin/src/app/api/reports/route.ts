import { NextResponse } from 'next/server';

export async function GET() {
    return NextResponse.json({ message: 'Feature removed' }, { status: 404 });
}

export async function PATCH() {
    return NextResponse.json({ message: 'Feature removed' }, { status: 404 });
}

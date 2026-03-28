import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.BACKEND_URL || 'https://api.shortlovers.id/api';
const ADMIN_KEY = process.env.ADMIN_API_KEY || '';

// GET /api/users/[id]
export async function GET(
    _request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const res = await fetch(`${BACKEND}/admin/users/${id}`, {
            headers: { 'X-Admin-Key': ADMIN_KEY },
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Get user error:', error);
        return NextResponse.json({ message: 'Failed to fetch user' }, { status: 500 });
    }
}

// PATCH /api/users/[id]
export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const body = await request.json();
        const res = await fetch(`${BACKEND}/admin/users/${id}`, {
            method: 'PATCH',
            headers: { 'X-Admin-Key': ADMIN_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Update user error:', error);
        return NextResponse.json({ message: 'Failed to update user' }, { status: 500 });
    }
}

// DELETE /api/users/[id]
export async function DELETE(
    _request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const res = await fetch(`${BACKEND}/admin/users/${id}`, {
            method: 'DELETE',
            headers: { 'X-Admin-Key': ADMIN_KEY },
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
    } catch (error) {
        console.error('Delete user error:', error);
        return NextResponse.json({ message: 'Failed to delete user' }, { status: 500 });
    }
}

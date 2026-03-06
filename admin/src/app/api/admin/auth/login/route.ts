import { NextRequest, NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import prisma from '@/lib/prisma';
import { generateToken } from '@/lib/auth';

// POST /api/admin/auth/login
export async function POST(request: NextRequest) {
    try {
        const { email, password } = await request.json();

        if (!email || !password) {
            return NextResponse.json(
                { message: 'Email and password are required' },
                { status: 400 }
            );
        }

        // Find user
        const user = await prisma.user.findUnique({ where: { email } });
        if (!user || !user.password) {
            return NextResponse.json(
                { message: 'Invalid credentials' },
                { status: 401 }
            );
        }

        // Verify password
        const isValid = await bcrypt.compare(password, user.password);
        if (!isValid) {
            return NextResponse.json(
                { message: 'Invalid credentials' },
                { status: 401 }
            );
        }

        // Verify Role
        if (user.role !== 'admin') {
            return NextResponse.json(
                { message: 'Access denied. Administrator privileges required.' },
                { status: 403 }
            );
        }

        // Generate token
        // Generate token
        const token = generateToken({
            id: user.id,
            role: user.role,
        });

        // Remove password
        const { password: _, ...userWithoutPassword } = user;

        return NextResponse.json({ token, user: userWithoutPassword }, { status: 200 });
    } catch (error) {
        console.error('Admin Login error:', error);
        return NextResponse.json(
            { message: 'Login failed' },
            { status: 500 }
        );
    }
}

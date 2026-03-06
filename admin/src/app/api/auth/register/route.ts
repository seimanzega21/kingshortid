import { NextRequest, NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import prisma from '@/lib/prisma';
import { generateToken } from '@/lib/auth';

// POST /api/auth/register
export async function POST(request: NextRequest) {
    try {
        const { name, email, password } = await request.json();

        // Validate
        if (!name || !email || !password) {
            return NextResponse.json(
                { message: 'Name, email and password are required' },
                { status: 400 }
            );
        }

        if (password.length < 6) {
            return NextResponse.json(
                { message: 'Password must be at least 6 characters' },
                { status: 400 }
            );
        }

        // Check existing
        const existing = await prisma.user.findUnique({ where: { email } });
        if (existing) {
            return NextResponse.json(
                { message: 'Email already registered' },
                { status: 400 }
            );
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 10);

        // Create user
        const user = await prisma.user.create({
            data: {
                name,
                email,
                password: hashedPassword,
                provider: 'local',
                coins: 200, // Registration bonus
            },
        });

        // Record bonus transaction
        await prisma.coinTransaction.create({
            data: {
                userId: user.id,
                type: 'bonus',
                amount: 200,
                description: 'Bonus registrasi berhasil',
                balanceAfter: 200,
            },
        });

        // Generate token
        const token = generateToken({
            id: user.id,
            role: user.role,
        });

        // Remove password from response
        const { password: _, ...userWithoutPassword } = user;

        return NextResponse.json({ token, user: userWithoutPassword }, { status: 201 });
    } catch (error) {
        console.error('Register error:', error);
        return NextResponse.json(
            { message: 'Registration failed' },
            { status: 500 }
        );
    }
}

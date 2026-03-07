import { Hono } from 'hono';
import { eq, and } from 'drizzle-orm';
import bcrypt from 'bcryptjs';
import { getDb } from '../db';
import { users, coinTransactions } from '../db/schema';
import { Env, generateToken, getAuthUser, requireAuth } from '../middleware/auth';

const auth = new Hono<Env>();

// POST /api/auth/login
auth.post('/login', async (c) => {
    try {
        const { email, password } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const user = await db.select().from(users).where(eq(users.email, email)).limit(1).then((r: any[]) => r[0]);
        if (!user) return c.json({ message: 'User tidak ditemukan' }, 401);
        if (!user.password) return c.json({ message: 'Login method tidak valid' }, 401);

        const isValid = await bcrypt.compare(password, user.password);
        if (!isValid) return c.json({ message: 'Password salah' }, 401);

        const token = await generateToken(c, { id: user.id, role: user.role });

        const { password: _, ...userWithoutPassword } = user;
        return c.json({
            token,
            user: {
                ...userWithoutPassword,
                coins: user.coins,
                vipStatus: user.vipStatus,
                vipExpiry: user.vipExpiry,
            },
        });
    } catch (error) {
        console.error('Login error:', error);
        return c.json({ message: 'Login Error' }, 500);
    }
});

// POST /api/auth/register
auth.post('/register', async (c) => {
    try {
        const { name, email, password } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!name || !email || !password) {
            return c.json({ message: 'Name, email and password are required' }, 400);
        }

        if (password.length < 6) {
            return c.json({ message: 'Password minimal 6 karakter' }, 400);
        }

        const existing = await db.select().from(users).where(eq(users.email, email)).limit(1).then((r: any[]) => r[0]);
        if (existing) return c.json({ message: 'Email sudah terdaftar' }, 400);

        const hashedPassword = await bcrypt.hash(password, 10);
        const numericId = Math.floor(10000000000 + Math.random() * 90000000000).toString();

        const [user] = await db.insert(users).values({
            name,
            email,
            password: hashedPassword,
            provider: 'local',
            guestId: numericId,
            isGuest: false,
            coins: 100,
        }).returning();

        await db.insert(coinTransactions).values({
            userId: user.id,
            type: 'bonus',
            amount: 100,
            description: 'Welcome bonus',
            balanceAfter: 100,
        });

        const token = await generateToken(c, { id: user.id, role: user.role });
        const { password: _, ...userWithoutPassword } = user;

        return c.json({ token, user: userWithoutPassword }, 201);
    } catch (error) {
        console.error('Register error:', error);
        return c.json({ message: 'Registration failed' }, 500);
    }
});

// GET /api/auth/me
auth.get('/me', async (c) => {
    try {
        const user = await getAuthUser(c);
        if (!user) return c.json({ error: 'Unauthorized' }, 401);

        // Fire-and-forget: touch updatedAt as heartbeat for "Online" tracking
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        db.update(users).set({ updatedAt: new Date() }).where(eq(users.id, user.id)).catch(() => { });

        const { password: _, ...userWithoutPassword } = user;
        return c.json(userWithoutPassword);
    } catch (error) {
        console.error('Get me error:', error);
        return c.json({ error: 'Failed to get user' }, 500);
    }
});

// PUT /api/auth/me - Update profile
auth.put('/me', requireAuth, async (c) => {
    try {
        const user = c.get('user');
        const { name, avatar, currentPassword, newPassword } = await c.req.json();
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        const updateData: Record<string, any> = {};
        if (name) updateData.name = name;
        if (avatar !== undefined) updateData.avatar = avatar;

        if (newPassword) {
            if (!currentPassword) {
                return c.json({ message: 'Password saat ini diperlukan' }, 400);
            }
            if (!user.password) {
                return c.json({ message: 'Akun ini tidak menggunakan password' }, 400);
            }
            const isValid = await bcrypt.compare(currentPassword, user.password);
            if (!isValid) {
                return c.json({ message: 'Password saat ini salah' }, 400);
            }
            updateData.password = await bcrypt.hash(newPassword, 10);
        }

        if (Object.keys(updateData).length === 0) {
            return c.json({ message: 'Tidak ada data yang diubah' }, 400);
        }

        updateData.updatedAt = new Date();

        const [updatedUser] = await db.update(users)
            .set(updateData)
            .where(eq(users.id, user.id))
            .returning();

        const { password: _, ...userWithoutPassword } = updatedUser;
        return c.json({ user: userWithoutPassword, message: 'Profil berhasil diperbarui' });
    } catch (error) {
        console.error('Update profile error:', error);
        return c.json({ message: 'Gagal memperbarui profil' }, 500);
    }
});

// POST /api/auth/guest
auth.post('/guest', async (c) => {
    try {
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);
        const guestId = Math.floor(10000000000 + Math.random() * 90000000000).toString();
        const guestEmail = `guest_${guestId}@kingshort.local`;

        const [user] = await db.insert(users).values({
            email: guestEmail,
            name: `Penonton ${guestId.slice(-4)}`,
            provider: 'guest',
            guestId,
            isGuest: true,
            coins: 50,
        }).returning();

        await db.insert(coinTransactions).values({
            userId: user.id,
            type: 'bonus',
            amount: 50,
            description: 'Guest welcome bonus',
            balanceAfter: 50,
        });

        const token = await generateToken(c, { id: user.id, role: user.role });

        // Fire-and-forget: heartbeat for "Online" tracking
        db.update(users).set({ updatedAt: new Date() }).where(eq(users.id, user.id)).catch(() => { });

        return c.json({
            token,
            user: {
                id: user.id,
                guestId: user.guestId,
                name: user.name,
                isGuest: true,
                coins: user.coins,
                vipStatus: user.vipStatus,
            },
        });
    } catch (error) {
        console.error('Guest registration error:', error);
        return c.json({ message: 'Failed to create guest account' }, 500);
    }
});

// POST /api/auth/upgrade
auth.post('/upgrade', requireAuth, async (c) => {
    try {
        const user = c.get('user');
        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        if (!user.isGuest) {
            return c.json({ message: 'Account is already upgraded' }, 400);
        }

        const { name, email, password } = await c.req.json();

        if (!name || !email || !password) {
            return c.json({ message: 'Name, email and password are required' }, 400);
        }

        const existing = await db.select().from(users).where(eq(users.email, email)).limit(1).then((r: any[]) => r[0]);
        if (existing) return c.json({ message: 'Email sudah terdaftar' }, 400);

        const hashedPassword = await bcrypt.hash(password, 10);

        const [updatedUser] = await db.update(users)
            .set({
                name,
                email,
                password: hashedPassword,
                provider: 'local',
                isGuest: false,
                coins: user.coins + 50,
                updatedAt: new Date(),
            })
            .where(eq(users.id, user.id))
            .returning();

        await db.insert(coinTransactions).values({
            userId: updatedUser.id,
            type: 'bonus',
            amount: 50,
            description: 'Account upgrade bonus',
            balanceAfter: updatedUser.coins,
        });

        const token = await generateToken(c, { id: updatedUser.id, role: updatedUser.role });
        const { password: _, ...userWithoutPassword } = updatedUser;

        return c.json({
            token,
            user: userWithoutPassword,
            message: 'Account upgraded successfully',
        });
    } catch (error) {
        console.error('Upgrade error:', error);
        return c.json({ message: 'Failed to upgrade account' }, 500);
    }
});

// POST /api/auth/google
auth.post('/google', async (c) => {
    try {
        const { idToken, accessToken } = await c.req.json();
        if (!idToken && !accessToken) return c.json({ message: 'idToken atau accessToken diperlukan' }, 400);

        let googleUser: { sub: string; email: string; name: string; picture: string };

        if (idToken) {
            // Verify Google ID token
            const googleRes = await fetch(`https://oauth2.googleapis.com/tokeninfo?id_token=${idToken}`);
            if (!googleRes.ok) return c.json({ message: 'Token Google tidak valid' }, 401);
            googleUser = await googleRes.json() as any;
        } else {
            // Use access token to get user info
            const googleRes = await fetch('https://www.googleapis.com/userinfo/v2/me', {
                headers: { Authorization: `Bearer ${accessToken}` },
            });
            if (!googleRes.ok) return c.json({ message: 'Token Google tidak valid' }, 401);
            const info = await googleRes.json() as any;
            googleUser = { sub: info.id, email: info.email, name: info.name, picture: info.picture };
        }
        const { sub: googleId, email, name, picture } = googleUser;
        if (!email) return c.json({ message: 'Email tidak ditemukan di akun Google' }, 400);

        const db = getDb(c.env.SUPABASE_URL, c.env.SUPABASE_DB_PASSWORD);

        // Check existing user by email or providerId
        let user = await db.select().from(users).where(eq(users.email, email)).limit(1).then((r: any[]) => r[0]);

        if (user) {
            // Link Google to existing local account
            if (user.provider === 'local' || !user.providerId) {
                [user] = await db.update(users)
                    .set({ provider: 'google', providerId: googleId, avatar: user.avatar || picture || null, updatedAt: new Date() })
                    .where(eq(users.id, user.id))
                    .returning();
            }
            if (!user.isActive) return c.json({ message: 'Akun dinonaktifkan' }, 403);
        } else {
            // Create new user
            const numericId = Math.floor(10000000000 + Math.random() * 90000000000).toString();
            [user] = await db.insert(users).values({
                email,
                name: name || email.split('@')[0],
                avatar: picture || null,
                provider: 'google',
                providerId: googleId,
                guestId: numericId,
                isGuest: false,
                coins: 200,
            }).returning();

            await db.insert(coinTransactions).values({
                userId: user.id,
                type: 'bonus',
                amount: 200,
                description: 'Bonus registrasi Google',
                balanceAfter: 200,
            });
        }

        const token = await generateToken(c, { id: user.id, role: user.role });

        // Fire-and-forget: heartbeat for "Online" tracking
        db.update(users).set({ updatedAt: new Date() }).where(eq(users.id, user.id)).catch(() => { });
        const { password: _, ...userWithoutPassword } = user;

        return c.json({ token, user: { ...userWithoutPassword, coins: user.coins, vipStatus: user.vipStatus, vipExpiry: user.vipExpiry } });
    } catch (error) {
        console.error('Google auth error:', error);
        return c.json({ message: 'Login Google gagal' }, 500);
    }
});



export default auth;

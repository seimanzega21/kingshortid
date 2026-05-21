# KingShort Security & Bug Fixes Plan

## Goal
Implement robust authorization controls in the CF-Backend Hono APIs, secure the Next.js Admin Panel API proxy via cookie validation, prevent Midtrans webhook spoofing, and fix the mobile client AuthContext crash.

## Tasks
- [ ] Task 1: Secure Next.js Admin Panel Login/Logout & Cookies → Verify: Add `admin_token` httpOnly cookie in `/api/admin/auth/login` and clear it in new `/api/admin/auth/logout` endpoint. Update logout onClick in `Sidebar.tsx`.
- [ ] Task 2: Validate Admin Session in Next.js Middleware → Verify: Implement Web Crypto JWT verification in `admin/src/middleware.ts` to block unauthorized requests and inject `X-Admin-Key` only for verified admin tokens. Automatically extend (sliding expiration) the `admin_token` cookie on successful requests.
- [ ] Task 3: Secure Hono Backend Write Routes → Verify: Apply the existing `requireAdmin` middleware to all POST, PATCH, DELETE endpoints in `cf-backend/src/routes/dramas.ts`, `episodes.ts`, and `settings.ts`.
- [ ] Task 4: Secure VIP Stream Endpoint → Verify: Update `GET /api/episodes/:id/stream` in `episodes.ts` to decode/verify user JWT and return 403 if user is not VIP.
- [ ] Task 5: Verify Midtrans Webhook Signatures → Verify: Implement SHA-512 signature key verification in `cf-backend/src/routes/webhooks.ts` using `MIDTRANS_SERVER_KEY` before processing top-ups.
- [ ] Task 6: Fix Mobile Client AuthContext Reference Error → Verify: Import `storeAuthData` in `mobile/context/AuthContext.tsx` and retrieve `authToken` from `SecureStore` asynchronously inside `updateUser` and `refreshUser` to eliminate `cachedToken` ReferenceError.
- [ ] Task 7: Verification and Audit Run → Verify: Run `python .agent/scripts/checklist.py .` to ensure all tests, security scans, and lint checks pass.

## Done When
- [ ] Next.js Admin Panel rewrites are protected and only proxy requests for authenticated admin users.
- [ ] CF-Backend modification APIs (dramas, episodes, settings) return 403/401 for requests without admin access.
- [ ] VIP stream URL endpoint validates JWT token signature and VIP status.
- [ ] Midtrans webhooks validate SHA-512 signature.
- [ ] Mobile client profile updates and refresh calls execute successfully without crash.
- [ ] Validation scripts pass with zero critical vulnerabilities.

## Notes
- Token verification in Next.js middleware is implemented using native `crypto.subtle` (Web Crypto) to guarantee compatibility with edge and serverless runtimes.
- Admin token cookie uses `httpOnly`, `secure` (in production), and `sameSite: 'strict'` to prevent XSS/CSRF.
- Midtrans signature matches raw `gross_amount` string from payload.

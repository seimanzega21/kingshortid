# Schema Management Guide

## Source of Truth
The **admin** project contains the source of truth for the Prisma schema:
```
d:\kingshortid\admin\prisma\schema.prisma
```

## Workflow for Schema Changes

1. **Always edit the admin schema first**
2. Run validation: `cd admin && npx prisma validate`
3. Copy changes to backend schema
4. Run validation: `cd backend && npx prisma validate`
5. Apply migrations: `npx prisma db push` (or `npx prisma migrate dev`)

## Why Two Schemas?
Both `admin` (Next.js) and `backend` (Express) need their own Prisma client for:
- Different build processes
- Independent deployments
- Framework-specific configurations

## Validation Commands
```powershell
# Validate admin schema
cd d:\kingshortid\admin && npx prisma validate

# Validate backend schema  
cd d:\kingshortid\backend && npx prisma validate
```

## Last Synced
- **Date**: 2026-01-30
- **Status**: ✅ Both schemas match

# Build Stage
FROM node:20-alpine AS builder
RUN apk add --no-cache openssl
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy Prisma schema and generate client
COPY prisma ./prisma/
RUN npx prisma generate

# Copy source code and build Next.js app
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV JWT_SECRET="dummy-jwt-secret-min-32-characters-for-build-stage-only"
ENV DATABASE_URL="postgresql://dummy:dummy@localhost:5432/dummy"
ENV ADMIN_API_KEY="dummy-admin-api-key-for-build-stage-only"
RUN npm run build

# Production Stage
FROM node:20-alpine AS runner
RUN apk add --no-cache openssl
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Copy package and node_modules
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/prisma ./prisma

EXPOSE 3000
CMD ["npm", "run", "start"]

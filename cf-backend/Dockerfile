FROM oven/bun:1.2-alpine AS builder
WORKDIR /app

# Install dependencies
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile

# Copy source
COPY tsconfig.json ./
COPY src/ ./src/

# Production image
FROM oven/bun:1.2-alpine
WORKDIR /app

# Copy node_modules and source from builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/src ./src
COPY package.json tsconfig.json ./

# Non-root user for security
RUN adduser -D -u 1001 appuser && chown -R appuser /app
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["bun", "run", "src/server.ts"]

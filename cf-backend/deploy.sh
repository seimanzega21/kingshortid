#!/bin/bash
# deploy.sh — KingShortID API VPS Deployment Script
# Jalankan di VPS via Coolify Terminal atau SSH

set -e

echo "🚀 KingShortID API — VPS Deployment"
echo "======================================"

REPO_DIR="/opt/kingshortid-api"
GITHUB_URL="https://github.com/seimanzega21/kingshortid.git"

# 1. Clone atau pull repo
if [ -d "$REPO_DIR/.git" ]; then
    echo "📥 Pulling latest code..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "📥 Cloning repo..."
    mkdir -p /opt
    git clone "$GITHUB_URL" "$REPO_DIR"
fi

cd "$REPO_DIR/cf-backend"

# 2. Validasi .env.production ada sebelum deploy
if [ ! -f ".env.production" ]; then
    echo "❌ ERROR: .env.production tidak ditemukan!"
    echo "   Salin .env.example ke .env.production dan isi semua nilai."
    exit 1
fi

# 3. Build & run (satu kali saja)
echo "🐳 Building Docker image..."
docker compose build --no-cache

echo "🟢 Starting container..."
docker compose up -d

echo ""
echo "✅ Deploy selesai!"
echo "   Health: curl http://localhost:3000/health"
echo ""
docker compose ps

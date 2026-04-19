# VPS Deployment Guide

Self-hosted production deployment with Docker Compose + nginx reverse proxy.

## Server requirements

- **OS:** Ubuntu 22.04 / Debian 12 (or any Linux with Docker)
- **CPU:** 2 vCPU minimum (4 recommended)
- **RAM:** 4 GB minimum (EasyOCR + WebKit are hungry; 8 GB recommended)
- **Disk:** 10 GB free (Docker images + image cache)
- **Network:** open ports 80 + 443 (nginx)

## One-time setup

```bash
# On your VPS
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER && newgrp docker

# Clone
git clone <your-repo-url> vine_rec
cd vine_rec

# Configure
cp .env.example .env
vim .env   # set OPENROUTER_API_KEY at minimum
```

## First boot

```bash
# Build + start everything (this takes ~10-15 min the first time —
# Playwright WebKit + EasyOCR models bake into the image)
docker compose up -d --build

# Watch the backend warm up (look for "EasyOCR reader ready")
docker compose logs -f backend
```

When you see `Application startup complete.` the API is ready.

## Verify

```bash
# Health check
curl http://localhost/api/health

# Open in browser:  http://YOUR_VPS_IP/
# - Overview          /
# - Single analyze    /analyze
# - Batch (10 SKUs)   /batch
# - History           /results
# - API docs          /docs
```

## TLS (recommended)

Drop your certs in `nginx/ssl/` and uncomment the 443 server block in
`nginx/nginx.conf`. Or front the whole stack with [Caddy](https://caddyserver.com/)
for automatic Let's Encrypt:

```bash
# Caddyfile
your-domain.com {
  reverse_proxy localhost:80
}
```

## Updating

```bash
git pull
docker compose up -d --build
```

Backend reloads (warming the EasyOCR model takes ~5s on first request).

## Operations

```bash
# Tail logs
docker compose logs -f --tail=100

# Restart just one service
docker compose restart backend

# Inspect run history (SQLite is mounted at ./data/)
sqlite3 data/runs.db "SELECT verdict, COUNT(*) FROM runs GROUP BY verdict"

# Clear cached images (to force re-download)
rm -rf data/images/* data/cache/*
```

## Resource notes

- The backend runs **1 uvicorn worker** by default. The pipeline holds a
  shared Playwright WebKit browser + EasyOCR model in memory; multiple
  workers = multiplied memory cost. Bump to 2 workers in `backend/Dockerfile`
  only if you have ≥ 8 GB RAM.
- WebKit needs `shm_size: 1g` (already set in `docker-compose.yml`) to avoid
  shared-memory crashes.
- Run history grows in `data/runs.db`. It's safe to vacuum or delete.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Bing search error` in logs | WebKit failed to launch | Increase `shm_size`, check container memory limit |
| All wines return `NO_IMAGE` with confidence 0 | OpenRouter key missing/invalid | Check `OPENROUTER_API_KEY` in `.env`, restart backend |
| Frontend can't reach API | `NEXT_PUBLIC_API_URL` wrong | Inside Docker it must be `http://backend:8000/api` (already set) |
| `502 Bad Gateway` from nginx | Backend not yet healthy | Wait 60s for warmup; `docker compose ps` should show `healthy` |
| Per-SKU latency > 2 min | OCR running on CPU + sequential | Already optimized; see `ANALYSIS_CONCURRENCY` env var |

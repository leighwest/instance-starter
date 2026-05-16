# instance-starter

A Django application for managing AWS EC2 instances via a web UI. Supports real-time status updates via WebSockets, background task processing with Celery, and a dark-themed responsive UI.

The infrastructure is managed in a companion repo: [instance-starter-infra](https://github.com/leighwest/instance-starter-infra).

**Live site:** https://instance-starter.leighwest.dev

---

## What it does

- Start and stop EC2 instances from a web interface
- Real-time status updates via WebSockets — no page refresh required
- Per-second countdown timer with progress bar for running instances
- Application health check via server-side proxy to avoid mixed content issues
- Tag-based EC2 instance discovery — instances seeded into the database via AWS tag filter, no hardcoded IDs in code
- Background task processing with Celery
- Scheduled status broadcasts every 10 seconds via Celery Beat

---

## Tech stack

| Layer | Technology |
|---|---|
| Framework | Django 5.1.2, Python 3.11 |
| ASGI server | Daphne |
| WebSockets | Django Channels |
| Task queue | Celery + Celery Beat |
| Database | PostgreSQL 14 |
| Cache / broker | Redis 7 |
| Containerisation | Docker Compose |
| Reverse proxy | Nginx |
| Cloud provider | AWS (EC2 management target) |
| Image registry | GitHub Container Registry (GHCR) |
| CI/CD | GitHub Actions (two-job: build + deploy) |

---

## Repository structure

```
instance-starter/          # this repo — application code
instance-starter-infra/    # separate repo — Terraform + cloud-init
```

Key files in this repo:

- `instance_starter/settings.py` — Django settings, all config via environment variables
- `docker-compose.yaml` — 5 services: db, redis, web, celery_worker, celery_beat
- `docker/Dockerfile.web` — Django app container
- `ec2_starter/models.py` — EC2 instance registry model
- `ec2_starter/service/ec2_service.py` — AWS operations, Celery tasks, WebSocket broadcasts
- `ec2_starter/management/commands/ensure_superuser.py` — idempotent superuser creation
- `ec2_starter/management/commands/sync_instances.py` — tag-based EC2 discovery and DB sync
- `.env.example` — environment variable template
- `.github/workflows/deploy.yml` — two-job CI/CD pipeline (build on GitHub, deploy via self-hosted runner)

---

## Running locally

```bash
git clone https://github.com/leighwest/instance-starter.git
cd instance-starter
cp .env.example .env
# fill in .env with real AWS credentials and local DB config
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
docker-compose exec web python manage.py ensure_superuser
docker-compose exec web python manage.py sync_instances
```

The app will be available at http://localhost:8000.

A `docker-compose.override.yml` is included for local development — it replaces the GHCR image reference with a local build.

---

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full production deployment instructions, including Terraform provisioning, GHCR image registry, CI/CD pipeline, and SSL setup.

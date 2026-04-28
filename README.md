# instance-starter

A Django application for managing AWS EC2 instance start/stop operations via a web UI. Uses WebSockets for real-time status updates and Celery for background tasks.

**Live site:** https://instance-starter.leighwest.dev

---

## What it does

- Start and stop EC2 instances from a web interface
- Real-time status updates via WebSockets (no page refresh required)
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
- `ec2_starter/models.py` — EC2 model
- `ec2_starter/management/commands/ensure_superuser.py` — idempotent superuser creation
- `.env.example` — environment variable template
- `.github/workflows/deploy.yml` — CI/CD pipeline

---

## Running locally

```bash
git clone https://github.com/leighwest/instance-starter.git
cd instance-starter
cp .env.example .env
# fill in .env with local values
docker-compose up -d
```

The app will be available at http://localhost:8000.

---

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full production deployment instructions, including Terraform provisioning, GHCR image registry, CI/CD pipeline, and SSL setup.
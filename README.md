# EC2 Instance Starter

A Django web application for starting and stopping AWS EC2 instances via a simple UI. Built to let people spin up my hobby projects on demand without leaving infrastructure running idle.

Live site: [instance-starter.leighwest.dev](https://instance-starter.leighwest.dev)

## What it does

- Start and stop EC2 instances from a web UI
- Real-time status updates via WebSockets
- Background task scheduling with Celery Beat
- Django admin for instance management

## Tech stack

- **App**: Django 5.1, Daphne (ASGI), Django Channels (WebSockets), Celery
- **Data**: PostgreSQL 14, Redis 7
- **Infra**: Vultr VPS, Terraform, cloud-init, Nginx, Let's Encrypt
- **CI/CD**: Self-hosted GitHub Actions runner

## Infrastructure

Zero-touch provisioning via Terraform and cloud-init — a single `terraform apply` provisions the VPS, configures Nginx, clones the repo, and starts all services. A self-hosted GitHub Actions runner handles continuous deployment on push to `main`.

See [instance-starter-infra](https://github.com/leighwest/instance-starter-infra) for the full infrastructure code.

## Local development

### Prerequisites

- Docker Desktop
- AWS credentials with EC2 permissions

### Setup

1. Clone the repo and copy the example env file:
```bash
    git clone https://github.com/leighwest/instance-starter
    cd instance-starter
    cp .env.example .env
```

2. Fill in your values in `.env` — AWS credentials and a Django secret key are required.

3. Start all services:
```bash
    docker-compose up -d
```

4. Run migrations and create a superuser:
```bash
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py ensure_superuser
```

5. Visit [http://localhost:8000](http://localhost:8000)

Django admin is available at `/admin` using the credentials from your `.env`.
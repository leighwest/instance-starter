# Deployment

Production deployment for instance-starter running on a Vultr VPS (Melbourne, 1GB RAM / 1 vCPU, $5/month).

---

## Architecture

```
Internet (port 80/443)
    ↓
Nginx (reverse proxy + SSL termination)
    ├─→ /static/ → /home/deployer/instance-starter/staticfiles/
    ├─→ /ws/     → localhost:8000 (WebSocket upgrade)
    └─→ /        → localhost:8000 (Django)
                      ↓
            Docker Compose (5 containers)
                ├─ web          (Django/Daphne on port 8000)
                ├─ db           (PostgreSQL 14)
                ├─ redis        (Redis 7)
                ├─ celery_worker (background tasks)
                └─ celery_beat  (scheduled broadcasts every 10s)
```

### CI/CD flow

```
git push → GitHub Actions (ubuntu-latest)
               ├─ build Docker image
               ├─ push to GHCR (ghcr.io/leighwest/instance-starter:latest)
               └─ trigger deploy job (self-hosted runner on server; no checkout step)
                      ├─ git pull --ff-only origin main (updates docker-compose.yaml)
                      ├─ docker-compose pull
                      ├─ docker-compose down && up -d
                      ├─ migrate
                      ├─ collectstatic
                      └─ sync_instances
```

---

## Infrastructure repos

| Repo | Purpose |
|---|---|
| `instance-starter` | Application code, Dockerfile, CI/CD workflow |
| `instance-starter-infra` | Terraform, cloud-init, Nginx config |

Key files in `instance-starter-infra` (local path on Kubuntu: `~/dev/instance-starter-infra`):

- `terraform/main.tf` — Vultr instance, SSH key, firewall, reserved IP. Uses `templatefile()` for cloud-init and a `locals` block to inject Nginx config
- `terraform/variables.tf` — all variables, secrets marked `sensitive = true`
- `terraform/terraform.tfvars` — real values, gitignored
- `terraform/terraform.tfvars.example` — safe-to-commit template
- `terraform/cloud-init.yml` — full zero-touch bootstrap template
- `terraform/outputs.tf` — outputs reserved IP, SSH command, site URL
- `terraform-iam/` — separate Terraform root for IAM Roles Anywhere (trust anchor, role, profile). State is in S3 (`instance-starter-infra-tfstate`, key `iam/terraform.tfstate`); `pki/ca.crt` is the public CA cert
- `nginx/instance-starter.conf` — Nginx reverse proxy config (read by Terraform, injected into cloud-init)

---

## Provisioning a new server

Provisioning is automated via Terraform + cloud-init, with one deliberate manual step for AWS credentials (see [AWS credentials](#aws-credentials-iam-roles-anywhere)). A `terraform apply` will:

1. Create a Vultr instance and attach the reserved IP
2. Run cloud-init, which installs Docker, Nginx, and UFW; creates the `deployer` user; writes `.env`; clones the repo; authenticates with GHCR; starts all containers; and registers the GitHub Actions runner
3. Run migrations, collectstatic, ensure_superuser, and sync_instances
4. Obtain a Let's Encrypt certificate via Certbot

```bash
cd ~/dev/instance-starter-infra/terraform
terraform plan
terraform apply
```

After `apply`, on a rebuilt server:

1. Install `aws_signing_helper` to `/usr/local/bin/`.
2. Copy `client.crt` and `client.key` to `/etc/instance-starter/aws/` (dir `0700`, owned by `deployer`; key `0600`), and create the `config` file described below.
3. Re-run `docker-compose -f docker-compose.yaml up -d` and `exec -T web python manage.py sync_instances`.

One known issue also remains — see Known Issues below.

---

## Environment variables

The `.env` file is rendered from `terraform/cloud-init.yml` by Terraform's `templatefile()` and written to the server via cloud-init. The values come from `terraform/terraform.tfvars` (gitignored); use `terraform.tfvars.example` as the reference. There are no AWS key variables: credentials come from Roles Anywhere (below).

```
DATABASE_NAME=instance_starter
DATABASE_USER=instance_starter_user
DATABASE_PASSWORD=<strong_password>
DATABASE_HOST=db
DATABASE_PORT=5432
DJANGO_SECRET_KEY=<generated_key>
DEBUG=False
ALLOWED_HOSTS=<reserved_ip>,instance-starter.leighwest.dev,localhost,127.0.0.1
AWS_REGION=ap-southeast-4
REDIS_URL=redis://redis:6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=<email>
DJANGO_SUPERUSER_PASSWORD=<password>
```

---

## SSH access

Key pair: ed25519 at `~/.ssh/instance_starter_deploy` (regenerated on Kubuntu on 2026-10-09 and added to `deployer`'s `authorized_keys` via the Vultr console). On a fresh provision, the public key is uploaded to Vultr via Terraform (`ssh_public_key_path`) and written to `authorized_keys` via cloud-init. `~/.ssh/config` has a `Host vultr` alias.

```bash
# SSH as deployer (for app operations)
ssh vultr
# or: ssh -i ~/.ssh/instance_starter_deploy deployer@139.84.203.187

# SSH as root (for system-level operations)
ssh -i ~/.ssh/instance_starter_deploy root@139.84.203.187
```

---

## AWS credentials (IAM Roles Anywhere)

The app has no long-lived AWS keys. The server holds an X.509 client cert (`CN=instance-starter`) signed by a private CA; `aws_signing_helper` exchanges it for 1-hour credentials for the role `instance-starter-app`, which can only describe, start and stop instances tagged `Role=instance-starter-toy` and write their `ExpirationTime` tag.

- **Server files:** `/usr/local/bin/aws_signing_helper`, and `/etc/instance-starter/aws/` containing `client.crt`, `client.key` and `config` (a profile `instance-starter` using `credential_process`; paths must be absolute).
- **Containers:** `web`, `celery_worker` and `celery_beat` set `AWS_CONFIG_FILE=/etc/instance-starter/aws/config` and `AWS_PROFILE=instance-starter`, and mount the helper and config dir read-only. boto3's default credential chain caches and refreshes the credentials.
- **Don't set `AWS_ACCESS_KEY_ID` in `.env`:** env-var keys take precedence over `credential_process`.
- **Cert rotation:** the client cert expires about 2027-10-04. Sign a new one with the CA (key held offline in a password manager) and replace `client.crt`/`client.key`; no AWS change is needed.
- **AWS side:** managed in `instance-starter-infra/terraform-iam/` (trust anchor from `pki/ca.crt`, role, profile).

---

## Reserved IP

`139.84.203.187` is a Vultr reserved IP — permanent, survives `terraform destroy && apply`. This eliminates the ALLOWED_HOSTS chicken-and-egg problem (IP is known before provisioning). Managed as `vultr_reserved_ip.main` in Terraform.

---

## Domain & SSL

- Domain: `instance-starter.leighwest.dev` — A record in Cloudflare DNS (managed by the `dns-infra` repo) pointing to `139.84.203.187`
- Certificate: Let's Encrypt, obtained via Certbot during cloud-init
- Auto-renewal: `certbot.timer` systemd timer
- HTTP → HTTPS redirect: handled by Nginx (added by Certbot)
- Certificate files: `/etc/letsencrypt/live/instance-starter.leighwest.dev/`

---

## GHCR image registry

Docker images are built by GitHub Actions and pushed to `ghcr.io/leighwest/instance-starter:latest`. The server pulls the pre-built image on every deploy — no build step runs on the server.

GHCR authentication is handled automatically during provisioning — cloud-init runs `docker login ghcr.io` as the `deployer` user using a PAT injected via Terraform.

---

## Self-hosted GitHub Actions runner

The deploy job runs on a self-hosted runner installed as the `deployer` user on the server. The runner connects outbound to GitHub — no inbound firewall rules or SSH secrets in GitHub required.

Runner registration is handled automatically during provisioning — cloud-init fetches a registration token from the GitHub API and registers the runner using `config.sh --replace`, then installs and starts it as a systemd service.

```bash
# Runner management (on server)
cd /home/deployer/actions-runner
sudo ./svc.sh status
sudo ./svc.sh start
sudo ./svc.sh stop
```

---

## Common commands

```bash
# Terraform (main stack; IAM is in ../terraform-iam)
cd ~/dev/instance-starter-infra/terraform
terraform plan
terraform apply
terraform destroy

# Docker (on server, as deployer)
cd /home/deployer/instance-starter
docker-compose -f docker-compose.yaml ps
docker-compose -f docker-compose.yaml logs -f web
docker-compose -f docker-compose.yaml pull
docker-compose -f docker-compose.yaml down && docker-compose -f docker-compose.yaml up -d
docker-compose -f docker-compose.yaml exec -T web python manage.py ensure_superuser
docker-compose -f docker-compose.yaml exec -T web python manage.py sync_instances

# SSL
certbot certificates          # list certificates and expiry
certbot renew --dry-run       # test auto-renewal
systemctl status certbot.timer
```

---

## Known issues

- **Reserved IP detach error on destroy** — Vultr API errors when detaching reserved IP if the instance is already gone. Workaround: manually delete the reserved IP in the Vultr dashboard, then `terraform state rm vultr_reserved_ip.main` and re-apply.

---

## Key learnings

- **`$$` in Terraform templates** — `templatefile()` treats `$$` as an escaped `$`. Avoid `$` characters in secrets passed through templates.
- **cloud-init ordering** — `write_files` runs before `runcmd`. Cannot set `owner` on files referencing users not yet created.
- **Nginx config in cloud-init** — embed via Terraform `locals` + `file()` + `indent()` to avoid YAML parsing conflicts.
- **Docker Compose networking** — `DATABASE_HOST=db`, not `localhost` (Docker internal network).
- **Certbot owns listen directives** — don't define `listen 80` in the Nginx template; Certbot adds both port 80 and 443 blocks itself.
- **Certbot server_name requirement** — Certbot's nginx plugin matches on `server_name`, not the catch-all `_`. Must set the real domain before running Certbot.
- **ALLOWED_HOSTS includes domain** — browsers send the domain as the Host header once DNS is live. Must be in ALLOWED_HOSTS alongside the IP.
- **docker-compose restart vs down/up** — `restart` does not re-read `.env`. Use `down && up -d` when environment variables change.
- **Self-hosted runner direction** — runner connects outbound to GitHub. No inbound firewall rules or SSH secrets in GitHub required.
- **GHCR auth on server** — `GITHUB_TOKEN` in the workflow authenticates the GitHub-hosted runner to push. A separate classic PAT is needed for the server to pull — fine-grained tokens lack `read:packages` support.
- **Tag-based discovery** — filter instances by tag rather than hardcoding IDs; resilient to AMI rebuilds and instance recreation. Instance IDs are synced into the database via `sync_instances`.
- **Mixed content** — browsers block HTTP requests from HTTPS pages. Proxy health checks through Django to avoid this.
- **`docker-compose.override.yml` is auto-merged** — Docker Compose automatically merges any file named `docker-compose.override.yml` with the base file. Use explicit `-f docker-compose.yaml` in CI and cloud-init to prevent local dev overrides being picked up on the server.
- **GitHub Actions runner registration token** — fetch via POST to `/repos/{owner}/{repo}/actions/runners/registration-token` using a classic PAT with `repo` scope; parse with `python3` rather than `grep` to avoid fragile JSON string matching.
- **`config.sh --replace`** — prevents runner registration failing with "runner exists with same name" on reprovision.
- **`svc.sh` is generated by `config.sh`** — not present in the extracted runner archive; only appears after `config.sh` completes successfully.
- **The deploy job has no checkout** — the server's `docker-compose.yaml` only updates through `git pull --ff-only origin main` in the deploy script.
- **Missing bind-mount paths become directories** — Docker creates an empty directory for a host path that doesn't exist (as root). Create files such as the AWS config before `up`.
- **Env-var AWS keys beat `credential_process`** — remove them from `.env` or the role is never used.
- **cloud-init `cd` doesn't persist between list items** — each `-` item runs in a fresh subshell. Use a multiline `|` block for commands that depend on a working directory.
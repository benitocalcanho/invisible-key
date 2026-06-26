# Raspberry Pi Deployment Runbook

Use this checklist every time you deploy updates to the Raspberry Pi.

## 1) Optional: release local ngrok endpoint first

Run on your local machine only if your local app is running and may hold the same ngrok endpoint.

```bash
cd ~/Documents/Visual\ Studio\ Projects/Invisible\ Key
pkill -f "app.py" || true
pkill -f "ngrok" || true
ss -ltnp | grep 5000 || true
```

## 2) Open a shell on the Pi

Use SSH when you are on the same network or have another private route:

```bash
ssh pi@invisible-key.local
ssh pi@<pi-ip>
```

When you are away from the network, use **Raspberry Pi Connect** remote shell instead. This is the recommended recovery/admin path if you prepared the Pi with Raspberry Pi Imager.

## 3) Update app code on the Pi

Preferred production update command:

```bash
cd ~/invisible-key
./scripts/update-production.sh
```

This script runs the same Docker production update path shown below, then prints service status and recent logs. Wait for the GitHub Actions image build to finish before running it. If you run it too early, it may pull the previous image; run it again after the action completes.

Manual equivalent:

```bash
cd ~/invisible-key
git pull --ff-only origin main
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml pull app
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d --force-recreate app
```

Note: `docker-compose.prod.yml` uses prebuilt GHCR images. `git pull` updates compose/config files, while `pull` + `force-recreate` updates the running container image.

Do not use old local scripts that run `npm run build`, `pkill -f "python app.py"`, or `python app.py` on the Pi. Those were for pre-Docker/development use and do not update the production container.

## 4) Pull and restart production stack

Avoid building locally on Pi 2/3 unless you have a specific reason. If you must build from source instead of pulling the GHCR image:

```bash
docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d --build
```

## 5) Verify containers are healthy

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=200 app
```

## 6) Verify scheduler and timezone behavior

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=300 app | grep -Ei "Effective app timezone|Scheduler started|checkout|checkin|timezone"
```

Expected: log line includes effective timezone source (for example `source=system` or `source=config`) and scheduler startup details.

## 7) Verify GPIO startup and unlock logging

For GPIO-related changes, confirm the app warmed the relay output pins and logs pulse lifecycle events:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=200 app \
  | grep -aEi "GPIO output pins warmed|GPIO pulse start requested|GPIO pulse accepted|GPIO pulse ended|GPIO pulse failed"
```

Expected after startup:

```text
GPIO output pins warmed and forced inactive.
```

Expected after a door unlock attempt:

```text
GPIO pulse start requested: pin=17 ...
GPIO pulse accepted: pin=17 ...
GPIO pulse ended: pin=17 ...
```

## 8) Verify app endpoint

```bash
curl -I http://127.0.0.1:5000
```

## 9) Optional runtime introspection (scheduler and effective timezone)

```bash
docker exec -i invisible-key python - <<'PY'
from app import create_app
from services import calendar_service
app = create_app()
with app.app_context():
    print("APP_TIMEZONE:", app.config.get("APP_TIMEZONE"))
    print("EFFECTIVE_TIMEZONE:", app.config.get("EFFECTIVE_TIMEZONE"))
    s = calendar_service._scheduler
    print("scheduler running:", bool(s and s.running))
    if s:
        for j in s.get_jobs():
            print(j.id, j.next_run_time)
PY
```

## Troubleshooting shortcuts

If service name errors appear, confirm compose services:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml config --services
```

If your system only has the old Docker Compose binary, replace `docker compose` with `docker-compose`.

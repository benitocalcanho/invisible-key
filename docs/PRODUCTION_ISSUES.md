# Production Issues Log

This file records production incidents, evidence, and practical recovery notes. It is meant for real maintenance sessions, especially when working over SSH from a phone.

## 2026-07-06 Production Move And First Guest

### Context

The production SD card was moved between Raspberry Pi boards during onsite testing.

Known production commit at the end of the session:

```text
f943560 Translate unlock failure message
```

The running container at the end of the session:

```text
image=sha256:3ab92d2059f733e90af173eba4c9a4d944100a49232be400f14b271305be1821
started=2026-07-06T16:42:55.929892695Z
```

### Unsupported Raspberry Pi B Plus

The production SD card was temporarily booted in a Raspberry Pi Model B Plus Rev 1.2.

Diagnostics:

```text
uname -m: armv6l
model: Raspberry Pi Model B Plus Rev 1.2
container: restarting
exit code: 139
image architecture: arm
```

Cause:

The current Docker image supports newer ARM targets such as `linux/arm/v7`, `linux/arm64`, and `linux/amd64`. Raspberry Pi Model B Plus Rev 1.2 is ARMv6. The app container crashed with `exit=139`, consistent with running an unsupported image on ARMv6 hardware.

Production rule:

Do not use Raspberry Pi B Plus or Raspberry Pi Zero W v1.1 for the current Docker image. Use Raspberry Pi 2 B or newer compatible hardware.

### Container Stayed Down After Moving Back

To stop the crash loop on the unsupported Pi, the app container was stopped. After moving the SD card back into compatible hardware, Docker still treated the app as stopped.

Symptoms:

```text
docker compose ps showed only the table header
ss -ltnp showed nothing on :5000 or :4040
```

Recovery:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d --force-recreate app
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
```

Expected:

```text
invisible-key Up
0.0.0.0:5000->5000/tcp
```

### Power Loss Test

A hard power pull was discussed as a power outage simulation.

Guidance:

Only do this when onsite, when the app is idle, and after confirming the app is currently `Up`. Sudden power loss can still corrupt an SD card or SQLite database if it happens during a write.

Safer baseline before pulling power:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
```

After restoring power, wait 1 to 2 minutes, then check:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
hostname -I
ss -ltnp | grep -E ':5000|:4040' || true
```

### Emergency Unlock Scripts

The emergency scripts live in `/home/pi`, so they are easy to run immediately after SSH login.

Existing scripts:

```text
~/emergency_unlock.py
~/open-building
~/open-apartment
```

There is no `~/open-street` script.

Important behavior:

If the app is running, it may already own GPIO17 and GPIO27. Host scripts can fail with:

```text
lgpio.error: 'GPIO busy'
```

This is not a sudo permission problem. It is GPIO ownership. `sudo` cannot take the pin from the running app.

Phone-friendly emergency workflow:

```bash
./down
sudo ./building
sudo ./apartment
./up
```

Recommended helper scripts in `/home/pi`:

```bash
cp ~/app-down ~/down
cp ~/app-up ~/up
cp ~/open-building ~/building
cp ~/open-apartment ~/apartment
chmod +x ~/down ~/up ~/building ~/apartment
```

If those helper scripts do not exist yet, create `app-down` and `app-up` first:

```bash
cat > ~/app-down <<'SH'
#!/usr/bin/env bash
set -e
cd "$HOME/invisible-key"
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml stop app
echo "App stopped."
SH

cat > ~/app-up <<'SH'
#!/usr/bin/env bash
set -e
cd "$HOME/invisible-key"
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d app
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
SH

chmod +x ~/app-down ~/app-up
```

### First Guest Login Failure

The first guest could not log in from her iPhone. The same credentials worked from the admin's Android phone shortly after.

Audit screen evidence:

```text
19:24 to 19:27 Berlin time
username: franzisca
device: iPhone, Safari, iOS
language: de-DE
result: Login failed
```

Server log evidence:

```text
2026-07-06 17:24:20 UTC POST /api/auth/login 401 iPhone Safari
2026-07-06 17:24:29 UTC POST /api/auth/login 401 iPhone Safari
2026-07-06 17:24:41 UTC POST /api/auth/login 401 iPhone Safari
2026-07-06 17:24:53 UTC POST /api/auth/login 401 iPhone Safari
2026-07-06 17:27:11 UTC POST /api/auth/login 401 iPhone Safari

2026-07-06 17:29:56 UTC POST /api/auth/login 200 Android Chrome
2026-07-06 17:30:14 UTC POST /api/auth/login 200 Android Chrome
2026-07-06 17:30:31 UTC POST /api/auth/login 200 Android Chrome
```

Conclusion:

The app, ngrok, and login endpoint were working. The username was received correctly as `franzisca`. The most likely cause was the password submitted by the iPhone, such as hidden whitespace, autocapitalization, copy/paste artifact, wrong autofill value, or a visually similar character.

Implemented follow-up:

The app still does not log failed passwords. Failed login audit details now include safe diagnostic metadata:

```text
username
username length
password length
password starts with whitespace: yes/no
password ends with whitespace: yes/no
```

Do not log the password itself.

### Useful Commands From This Incident

Check repo commit:

```bash
cd ~/invisible-key
git rev-parse --short HEAD
git log -1 --oneline
```

Check running container:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
docker inspect invisible-key --format 'image={{.Image}} started={{.State.StartedAt}}'
```

Check login attempts:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=1000 app \
  | grep -aEi "POST /api/auth/login|401|200"
```

Check listening ports:

```bash
ss -ltnp | grep -E ':5000|:4040' || true
```

## 2026-07-26 Automatic Calendar Jobs Crashed After Schedule Change

### Context

The admin temporarily changed check-in time from `14:00` to `13:55`, then back to `14:00`, to allow early guest access. The manual **Sync Now** button later created/updated the guest successfully, but the automatic daily jobs did not complete.

Production state at diagnosis:

```text
CHECKOUT_TIME='12:00'
CHECKIN_TIME='14:00'
calendar guest: dirk, active, valid_until 2026-07-28
container uptime: Up 9 days
```

### Evidence

The scheduler did fire at the correct Berlin times, but both jobs crashed:

```text
2026-07-26 10:00:00 UTC Running job checkout_guests scheduled at 12:00 CEST
RuntimeError: Working outside of application context

2026-07-26 12:00:00 UTC Running job sync_calendar scheduled at 14:00 CEST
RuntimeError: Working outside of application context
```

Cause:

`start_scheduler(current_app)` could store Flask's `current_app` proxy in APScheduler job args. When APScheduler executed the job later outside a Flask request/app context, the proxy was unbound and `app.app_context()` failed.

### Recovery

Manual **Sync Now** from the admin dashboard still works because it runs inside an active Flask request context.

If this happens before the fix is deployed, use:

```text
Admin Dashboard -> Calendar Sync -> Sync Now
```

### Fix

`start_scheduler(app)` now resolves Flask `LocalProxy` objects immediately and schedules jobs with the concrete Flask app object. This keeps scheduled checkout and check-in jobs independent of the request context that restarted the scheduler.

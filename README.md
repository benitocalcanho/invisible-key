# Invisible Key — Automated Guest Access

Automated guest access for shared buildings. No keypads, no visible door changes.

Invisible Key is a plug-and-play **Raspberry Pi** web app for short-term rental hosts. Guests get a simple phone-friendly page to unlock building and apartment doors, while the admin dashboard manages users, WiFi, door images, logs, ngrok, email, and automatic guest rotation from a private iCal URL.

## Start Here

For a real Raspberry Pi installation, use the canonical guide:

- [docs/INSTALLATION.md](docs/INSTALLATION.md) — main Raspberry Pi install guide
- [docs/INSTALL_PI2B.md](docs/INSTALL_PI2B.md) — Raspberry Pi 2 B notes: 32-bit OS, USB WiFi, slower pulls
- [docs/INSTALL_PI3B.md](docs/INSTALL_PI3B.md) — Raspberry Pi 3 B/B+ notes
- [docs/DEPLOY_PI.md](docs/DEPLOY_PI.md) — repeatable update runbook
- [docs/HARDWARE.md](docs/HARDWARE.md) — relay and reed sensor wiring
- [docs/REMOTE_ACCESS.md](docs/REMOTE_ACCESS.md) — ngrok, Raspberry Pi Connect, Tailscale

## Quick Raspberry Pi Install

Use **Raspberry Pi Imager** first:

- Raspberry Pi 2 B / older 32-bit boards: Raspberry Pi OS Lite 32-bit
- Raspberry Pi 3/4/5: Raspberry Pi OS Lite 64-bit recommended
- set hostname, username/password, WiFi SSID/password, WiFi country, timezone, and keyboard
- enable SSH
- enable Raspberry Pi Connect if offered

On first boot, use the **Connect** button on the Raspberry Pi Connect website to open a shell. You can install without knowing the Pi IP address first.

On the Pi:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates
```

Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
sudo reboot
```

Raspberry Pi 2 B exception: use [docs/INSTALL_PI2B.md](docs/INSTALL_PI2B.md) for Docker installation. On Raspberry Pi OS Lite 32-bit Trixie, use `docker.io` / `docker-compose` from Raspberry Pi OS packages instead of Docker's upstream convenience script.

After reboot:

```bash
git clone https://github.com/benitocalcanho/invisible-key.git
cd invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d
```

Print the first local dashboard URL from the Raspberry Pi Connect shell:

```bash
printf 'Open this on your computer while on the same network: http://%s:5000\n' "$(hostname -I | awk '{print $1}')"
```

Open the printed local URL for first login. After ngrok is configured, use the ngrok URL as the normal admin and guest URL.

Default login:

```text
admin / admin12345
```

Change the admin password immediately, then configure iCal, ngrok, email, WiFi networks, and door images in the admin dashboard.

## Features

- **Guest dashboard** — full-screen phone-friendly door cards with one-tap unlock buttons
- **Automatic guest accounts** — daily iCal sync creates/removes guest accounts around check-in/check-out times
- **Cleaner handover** — cleaner account is active between guest stays and suspended during guest stays
- **Role-based access** — `admin`, `user`, `cleaner`, `guest`
- **Admin dashboard** — users, audit log, door log, button history, WiFi, ngrok, calendar, email, door images
- **Settings GUI** — configure operational secrets in the browser after install
- **GPIO relay control** — default 5-second relay pulse for each door
- **Door sensor log** — optional GPIO23 reed switch records open/closed changes
- **Remote access** — ngrok for web access; Raspberry Pi Connect or Tailscale for admin recovery shell
- **SD-card conscious logs** — Docker log rotation and app log retention defaults

## How Calendar Sync Works

The scheduler runs in the Raspberry Pi's local timezone unless `APP_TIMEZONE` explicitly overrides it.

| Time | Action |
|---|---|
| Check-out, default `12:00` | Re-checks iCal. If no event is active today, deletes calendar-created guest accounts and activates/creates cleaner. If an event still spans today, the guest account remains active. |
| Check-in, default `14:00` | Fetches iCal, finds events active today, creates/updates the guest account, and deactivates cleaner. |

Event title convention: the first word becomes the guest username. Password mode is configured in the dashboard.

## Hardware Defaults

| Function | BCM GPIO | Physical pin |
|---|---:|---:|
| Building door relay | GPIO17 | 11 |
| Apartment door relay | GPIO27 | 13 |
| Door reed sensor signal | GPIO23 | 16 |
| Reed sensor ground | GND | 14 |

Use [docs/HARDWARE.md](docs/HARDWARE.md) for wiring details.

## Updates

On the Pi:

```bash
cd ~/invisible-key
git pull --ff-only origin main
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml pull app
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d --force-recreate app
```

See [docs/DEPLOY_PI.md](docs/DEPLOY_PI.md) for the full deployment checklist.

## Desktop Development

Desktop/no-GPIO mode is for development only:

```bash
docker compose -f docker-compose.prod.yml up -d
```

For frontend/backend hot reload, see [docs/INSTALLATION.md](docs/INSTALLATION.md#desktop-development).

## Project Structure

```text
invisible-key/
├── backend/              # Flask API, SQLite models, services, GPIO, scheduler
├── frontend/             # Vue 3 SPA
├── docs/                 # Installation, deployment, hardware, remote access
├── scripts/              # Optional/manual setup helpers
├── systemd/              # Optional/manual service units
├── docker-compose.prod.yml
├── docker-compose.pi.yml
└── Dockerfile
```

## License

MIT

# Raspberry Pi Installation Guide

This is the canonical installation guide for Invisible Key on Raspberry Pi.

Use Docker. The app is published as a multi-architecture image for:

- `linux/arm/v7` — Raspberry Pi 2/3 with 32-bit OS
- `linux/arm64` — Raspberry Pi 3/4/5 with 64-bit OS
- `linux/amd64` — desktop/server development

Desktop/no-GPIO mode is documented at the end. For production Raspberry Pi installs, always include `docker-compose.pi.yml`.

## Documentation Map

| File | Purpose |
|---|---|
| [INSTALLATION.md](INSTALLATION.md) | Main Raspberry Pi install path |
| [INSTALL_PI2B.md](INSTALL_PI2B.md) | Pi 2 B-specific notes: 32-bit OS, USB WiFi, package Docker |
| [INSTALL_PI3B.md](INSTALL_PI3B.md) | Pi 3 B/B+-specific notes |
| [DEPLOY_PI.md](DEPLOY_PI.md) | Update/redeploy checklist |
| [HARDWARE.md](HARDWARE.md) | Relay and reed switch wiring |
| [REMOTE_ACCESS.md](REMOTE_ACCESS.md) | ngrok, Raspberry Pi Connect, Tailscale |

## 1. Prepare The SD Card

Use **Raspberry Pi Imager**.

| Raspberry Pi model | Recommended OS |
|---|---|
| Raspberry Pi 2 B / older 32-bit-only boards | Raspberry Pi OS Lite 32-bit |
| Raspberry Pi 3 B/B+ | Raspberry Pi OS Lite 64-bit preferred; 32-bit also works |
| Raspberry Pi 4/5 | Raspberry Pi OS Lite 64-bit |

Avoid Raspberry Pi OS Full/Desktop for production installs. Lite keeps the SD card cleaner and leaves more room for Docker images and logs.

Before writing the card, open **OS Customisation** and set:

| Setting | Recommended value |
|---|---|
| Hostname | `invisible-key` |
| Username/password | A normal Pi login, for example `pi` with a strong password |
| Wireless LAN | Primary WiFi SSID/password and WiFi country |
| Locale | Correct timezone, keyboard layout, and language |
| SSH | Enabled |
| Raspberry Pi Connect | Enabled/linked if Imager offers it |

Raspberry Pi Connect is a useful recovery/admin shell. It does not replace ngrok for guest web access.

## 2. First Boot

Boot the Pi and wait a minute or two for first-boot setup.

If you enabled Raspberry Pi Connect in Imager, go to the Raspberry Pi Connect website and press **Connect** for this device. That opens a browser shell; you do not need to know the Pi IP address just to begin installation.

SSH is still useful as a fallback when you are on the same network:

```bash
ssh pi@invisible-key.local
ssh pi@<pi-ip>
```

Install basic tools in the Raspberry Pi Connect shell or SSH shell:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates
```

For headless installs using Raspberry Pi Connect, enable user lingering so the user service can remain available after reboot before manual login:

```bash
loginctl enable-linger
```

## 3. Keep The Pi Awake 24/7

Invisible Key is a door access controller. It should not sleep.

Run this on Raspberry Pi OS Lite:

```bash
sudo raspi-config nonint do_blanking 1
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
sudo systemctl disable NetworkManager-wait-online.service
```

This applies to Pi 2, Pi 3, Pi 4, and Pi 5. The app, WiFi, ngrok, scheduler, and GPIO polling are expected to run continuously.

## 4. Install Docker

### Raspberry Pi 3/4/5

Use Docker's convenience script:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
sudo reboot
```

### Raspberry Pi 2 B

Do not use Docker's convenience script on Raspberry Pi OS Lite 32-bit Trixie. Use Raspberry Pi OS packages instead:

```bash
sudo rm -f /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
sudo reboot
```

See [INSTALL_PI2B.md](INSTALL_PI2B.md) for Pi 2 B details.

After reboot, verify:

```bash
docker --version
docker compose version
```

If your system only has the old Compose binary, use `docker-compose` instead of `docker compose`.

## 5. Install Invisible Key

Clone the app:

```bash
git clone https://github.com/benitocalcanho/invisible-key.git
cd invisible-key
```

Start the Raspberry Pi production stack:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d
```

The Pi overlay is required for:

- GPIO relay control
- GPIO23 reed sensor monitoring
- Admin WiFi management through host NetworkManager

Do not add `privileged: true` for normal operation. The Pi overlay maps only the needed host interfaces.

## 6. First Login

Get the Pi's local dashboard URL from the Raspberry Pi Connect shell or SSH shell:

```bash
printf 'Open this on your computer while on the same network: http://%s:5000\n' "$(hostname -I | awk '{print $1}')"
```

Open the printed URL, for example:

```text
http://192.168.1.123:5000
```

This local IP is mainly for first setup and troubleshooting. After ngrok is configured, use the ngrok URL as the normal admin URL too. That is the same stable URL guests will use.

Default login:

```text
admin / admin12345
```

Change the admin password immediately.

## 7. Configure In The Dashboard

After first login, configure operational settings in the admin dashboard.

| Setting | Dashboard area |
|---|---|
| Admin/users/cleaner accounts | Users |
| iCal URL | Calendar Sync |
| Guest password mode | Calendar Sync |
| Check-in / check-out times | Calendar Sync |
| ngrok token and static domain | ngrok Tunnel |
| SMTP notifications | E-Mail |
| Saved WiFi networks | WLAN/WiFi Networks |
| Door photos and crop/position | Door Images |
| Door reed sensor log | Door Log |

Only bootstrap values belong in environment variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask signing secret |
| `JWT_SECRET_KEY` | JWT signing secret |
| `ADMIN_USERNAME` | Initial admin username |
| `ADMIN_PASSWORD` | Initial admin password |
| `APP_TIMEZONE` | Optional IANA timezone override |

## 8. Remote Access

Use:

- **ngrok** for the normal guest and admin web URL
- **Raspberry Pi Connect** for first install, recovery, and admin remote shell
- **Tailscale** optionally for private VPN SSH/admin access

After you save the ngrok token/domain in the dashboard and the tunnel starts, switch your own admin habit to the ngrok URL. Keep the local IP URL for troubleshooting on the same network.

If you use Tailscale in production, disable key expiry for the Pi in the Tailscale admin dashboard after enrollment so it does not require re-authentication later.

See [REMOTE_ACCESS.md](REMOTE_ACCESS.md).

## 9. Verify

Check container status:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=200 app
```

Check the app locally on the Pi:

```bash
curl -I http://127.0.0.1:5000
```

Check effective timezone and scheduler logs:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=300 app | grep -Ei "Effective app timezone|Scheduler started|checkout|checkin|timezone"
```

## Persistent Data

Docker named volumes keep runtime data across container updates:

| Volume | Contents |
|---|---|
| `invisible_key_data` | SQLite database at `/app/backend/instance/data/invisible_key.db` |
| `invisible_key_uploads` | Door images uploaded through the dashboard |

Back up the database:

```bash
docker cp invisible-key:/app/backend/instance/data/invisible_key.db ./backup.db
```

Restore a database backup:

```bash
docker cp ./backup.db invisible-key:/app/backend/instance/data/invisible_key.db
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml restart app
```

## Updates

Use [DEPLOY_PI.md](DEPLOY_PI.md) for the full checklist.

Short version:

```bash
cd ~/invisible-key
git pull --ff-only origin main
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml pull app
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d --force-recreate app
```

## Logs And SD Card Protection

The Docker Compose files cap app container logs with Docker's `json-file` log driver:

```yaml
max-size: "5m"
max-file: "3"
```

The app also trims old database log rows by default:

| Log | Default retention |
|---|---:|
| Audit log | 180 days |
| Door sensor log | 90 days |

## WiFi Notes

Seed the primary WiFi during SD-card creation. Add or remove later networks from Admin -> WiFi Networks.

If the Pi will connect through a WiFi repeater/range extender, especially with a USB WiFi adapter, disable WiFi MAC randomization after first login. Some repeaters use MAC proxying, and local SSH/app access can fail even while ping works.

See [INSTALL_PI2B.md](INSTALL_PI2B.md#wifi-and-repeater-notes) for the exact NetworkManager setting. The same note can apply to Pi 3/4/5 when using a repeater.

## Optional Manual Install

Docker is the supported production path. The old setup scripts remain only for custom/manual installs:

```bash
sudo bash scripts/01-setup-pi.sh
sudo bash scripts/04-setup-ngrok.sh
sudo bash scripts/05-setup-services.sh
```

Use this path only when Docker is not available or when you intentionally want OS-level control.

## Optional Hotspot Script

The old public `/wifi-setup` page is disabled in production. The hotspot script is not part of the main deployment path.

Seed primary WiFi with Raspberry Pi Imager, then manage additional networks in Admin -> WiFi Networks.

```bash
sudo bash scripts/02-setup-hotspot.sh
```

## Desktop Development

Desktop/no-GPIO mode is for development only:

```bash
docker compose -f docker-compose.prod.yml up -d
```

For hot reload without Docker:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

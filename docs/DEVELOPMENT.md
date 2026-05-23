# Developer Notes

This page is for development, local testing, and custom/manual installs. Normal Raspberry Pi users should start with [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md).

## Supported Docker Images

The published app image supports:

- `linux/arm/v7` — Raspberry Pi 2/3 with 32-bit OS
- `linux/arm64` — Raspberry Pi 3/4/5 with 64-bit OS
- `linux/amd64` — desktop/server development

Production Raspberry Pi installs should use both Compose files:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d
```

Desktop/no-GPIO development can use only the production Compose file:

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Hot Reload Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Bootstrap Environment Variables

Only bootstrap values belong in environment variables. Operational settings such as ngrok, SMTP, iCal, WiFi, and door images are configured in the admin dashboard.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask signing secret |
| `JWT_SECRET_KEY` | JWT signing secret |
| `ADMIN_USERNAME` | Initial admin username |
| `ADMIN_PASSWORD` | Initial admin password |
| `APP_TIMEZONE` | Optional IANA timezone override |

## Optional Manual Install Scripts

Docker is the supported production path. The setup scripts remain for custom/manual installs and development experiments:

```bash
sudo bash scripts/01-setup-pi.sh
sudo bash scripts/04-setup-ngrok.sh
sudo bash scripts/05-setup-services.sh
```

Use this path only when Docker is not available or when you intentionally want OS-level control.

## Project Structure

```text
invisible-key/
├── backend/              # Flask API, SQLite models, services, GPIO, scheduler
├── frontend/             # Vue 3 SPA
├── docs/                 # User, admin, hardware, and developer docs
├── scripts/              # Optional/manual setup helpers
├── systemd/              # Optional/manual service units
├── docker-compose.prod.yml
├── docker-compose.pi.yml
└── Dockerfile
```

## Reference Docs

- [API.md](API.md)
- [GOOGLE_CALENDAR.md](GOOGLE_CALENDAR.md)
- [GPIO_PINOUT.md](GPIO_PINOUT.md)

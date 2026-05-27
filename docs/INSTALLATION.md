# Installation

This page is kept as a documentation hub so old links still work.

For a normal Raspberry Pi installation, use the beginner walkthrough:

- [Raspberry Pi Setup For Normal Users](RASPBERRY_PI_SETUP.md)

Then configure the app in the dashboard:

- [First Admin Dashboard Setup](ADMIN_DASHBOARD_SETUP.md)

## Normal User Path

1. Prepare the SD card with Raspberry Pi Imager.
2. Disable WiFi power saving for production reliability.
3. Install Docker and start Invisible Key.
4. Open the local admin dashboard once.
5. Configure ngrok, calendar, email, WiFi, and door images.
6. Optional but recommended: install Tailscale for private admin SSH/dashboard recovery.
7. Use the ngrok URL as the normal admin and guest URL.

The full step-by-step version is here: [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md).

## Useful Production Docs

| File | Purpose |
|---|---|
| [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) | Main beginner Raspberry Pi walkthrough |
| [ADMIN_DASHBOARD_SETUP.md](ADMIN_DASHBOARD_SETUP.md) | First dashboard setup with ngrok, Gmail SMTP, and Google Calendar iCal |
| [HARDWARE.md](HARDWARE.md) | Relay and reed sensor wiring |
| [INTERCOM.md](INTERCOM.md) | Relay wiring for the intercom and 12V AC apartment opener |
| [REMOTE_ACCESS.md](REMOTE_ACCESS.md) | Raspberry Pi Connect, ngrok, and Tailscale |
| [DEPLOY_PI.md](DEPLOY_PI.md) | Update/redeploy checklist |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Emergency SSH unlock scripts, GPIO busy recovery, and health checks |
| [INSTALL_PI2B.md](INSTALL_PI2B.md) | Raspberry Pi 2 B-specific notes |
| [INSTALL_PI3B.md](INSTALL_PI3B.md) | Raspberry Pi 3 B/B+-specific notes |

## Developer And Reference Docs

| File | Purpose |
|---|---|
| [DEVELOPMENT.md](DEVELOPMENT.md) | Desktop development, no-GPIO mode, manual scripts, environment variables |
| [API.md](API.md) | API reference |
| [GOOGLE_CALENDAR.md](GOOGLE_CALENDAR.md) | Detailed calendar behavior |
| [GPIO_PINOUT.md](GPIO_PINOUT.md) | Pin table reference |

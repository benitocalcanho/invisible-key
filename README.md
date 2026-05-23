# Invisible Key — Automated Guest Access

Invisible Key is a Raspberry Pi web app for short-term rental hosts who need reliable guest access without keypads, visible door changes, router configuration, or paid remote-access subscriptions.

Guests get a simple phone-friendly page to unlock the building and apartment doors. You get an admin dashboard for users, logs, WiFi, door photos, ngrok, email alerts, and automatic guest/cleaner rotation from a private Google Calendar iCal link.

## Why It Works Almost Anywhere

Invisible Key is built for real homes and rented apartments: normal WiFi, repeaters, mobile routers, CGNAT, and networks where you cannot touch the router.

It does **not** require:

- a public IP address
- router configuration
- port forwarding
- a private domain
- paid remote-access subscriptions

The normal setup uses free services:

1. **Raspberry Pi Connect** — first setup and emergency shell access.
2. **ngrok** — the public guest/admin web URL.
3. **Tailscale** — optional private admin access and recovery.

## What It Does

- **Guest door page** — full-screen phone layout with one-tap unlock buttons.
- **Admin dashboard** — users, audit log, door log, button history, WiFi, ngrok, calendar, email, and door images.
- **Calendar automation** — iCal sync creates guest accounts at check-in and removes them at check-out.
- **Cleaner handover** — cleaner access is active between guest stays and suspended during guest stays.
- **Always-on master users** — master users can always unlock doors and are not controlled by the calendar.
- **GPIO relay control** — Raspberry Pi GPIO pulses the door relays.
- **Door sensor log** — optional reed sensor records open/closed changes.
- **SD-card conscious logging** — container log rotation and database log retention are enabled by default.

## Start Here

For a normal Raspberry Pi installation, follow these in order:

1. [Raspberry Pi Setup For Normal Users](docs/RASPBERRY_PI_SETUP.md)
2. [First Admin Dashboard Setup](docs/ADMIN_DASHBOARD_SETUP.md)
3. [Hardware Wiring](docs/HARDWARE.md)

Useful after setup:

- [Remote Access](docs/REMOTE_ACCESS.md) — Raspberry Pi Connect, ngrok, and Tailscale.
- [Update Runbook](docs/DEPLOY_PI.md) — how to update the app later.
- [Raspberry Pi 2 B Notes](docs/INSTALL_PI2B.md) — 32-bit OS, USB WiFi, slower pulls.
- [Raspberry Pi 3 B/B+ Notes](docs/INSTALL_PI3B.md) — Pi 3-specific notes.

Developer and reference docs are separate:

- [Developer Notes](docs/DEVELOPMENT.md)
- [API Reference](docs/API.md)
- [Google Calendar Details](docs/GOOGLE_CALENDAR.md)
- [GPIO Pinout](docs/GPIO_PINOUT.md)

## Hardware Defaults

| Function | BCM GPIO | Physical pin |
|---|---:|---:|
| Building door relay | GPIO17 | 11 |
| Apartment door relay | GPIO27 | 13 |
| Door reed sensor signal | GPIO23 | 16 |
| Reed sensor ground | GND | 14 |

Use [docs/HARDWARE.md](docs/HARDWARE.md) before wiring anything.

## License

MIT

# Raspberry Pi 3 B/B+ Notes

Use [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for the main install walkthrough. This file only contains Raspberry Pi 3 B/B+-specific notes.

## What Is Different On Pi 3 B/B+

- Raspberry Pi OS Lite 64-bit is preferred.
- Raspberry Pi OS Lite 32-bit also works if you need it.
- Onboard WiFi is available, but Ethernet is still useful for recovery.
- Use a 5V / 2.5A power supply.
- Use a good 16 GB or larger microSD card.

The app is intended to run 24/7 on Pi 3 B/B+. Raspberry Pi OS Lite normally stays awake, but see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md#4-keep-the-pi-awake) for optional sleep-target hardening and checks.

## OS Selection

In Raspberry Pi Imager:

| Field | Value |
|---|---|
| Device | Raspberry Pi 3 |
| OS | Raspberry Pi OS Lite 64-bit preferred |
| Hostname | `invisible-key` |
| WiFi | Configure primary SSID/password |
| SSH | Enabled |

Avoid Raspberry Pi OS Full/Desktop on small SD cards. The desktop image leaves less room for Docker images and logs.

## Docker Install

Use Docker's convenience script:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
sudo reboot
```

After reboot:

```bash
docker --version
docker compose version
```

## App Install Command

Use the same Raspberry Pi compose command as every other Pi:

```bash
git clone https://github.com/benitocalcanho/invisible-key.git
cd invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d
```

The Pi overlay is required for:

- GPIO relays
- reed sensor monitoring
- dashboard WiFi management through host NetworkManager

## WiFi Notes

Pi 3 onboard WiFi is usually fine for production. If connecting through a repeater/range extender and SSH or app access fails while ping works, use the MAC randomization note in [INSTALL_PI2B.md](INSTALL_PI2B.md#wifi-and-repeater-notes). That issue is not Pi 2-specific; it can affect any Pi behind some repeaters.

## Quick Checks

Find the Pi IP:

```bash
hostname -I
```

Check the app:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=200 app
```

Open:

```text
http://<pi-ip>:5000
```

Default login:

```text
admin / admin12345
```

Change the admin password immediately.

## Hardware References

- Relay and reed switch wiring: [HARDWARE.md](HARDWARE.md)
- Pin assignment table: [GPIO_PINOUT.md](GPIO_PINOUT.md)
- Repeatable update runbook: [DEPLOY_PI.md](DEPLOY_PI.md)

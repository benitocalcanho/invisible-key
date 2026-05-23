# Raspberry Pi Setup For Normal Users

This is the beginner-friendly installation path. Follow this if you want to install Invisible Key on a Raspberry Pi and use it in production.

You do not need a public IP address, router access, port forwarding, or a private domain.

## What You Need

- Raspberry Pi 2 B, 3 B/B+, 4, or 5
- Good power supply
- 16 GB or larger microSD card, preferably a good/endurance card
- Raspberry Pi Imager on your computer
- WiFi name and password for the place where the Pi will run
- Free accounts for Raspberry Pi Connect and ngrok
- Optional but recommended: free Tailscale account

## 1. Prepare The SD Card

Open **Raspberry Pi Imager**.

Recommended OS:

| Raspberry Pi model | OS |
|---|---|
| Raspberry Pi 2 B | Raspberry Pi OS Lite 32-bit |
| Raspberry Pi 3 B/B+ | Raspberry Pi OS Lite 64-bit preferred; 32-bit also works |
| Raspberry Pi 4/5 | Raspberry Pi OS Lite 64-bit |

Use Raspberry Pi OS **Lite** for production. It is smaller and cleaner than the Desktop image.

Before writing the card, open **OS Customisation** and set:

| Setting | What to enter |
|---|---|
| Hostname | `invisible-key` |
| Username/password | Your Pi login, for example `pi` plus a strong password |
| Wireless LAN | Your main WiFi SSID/password and WiFi country |
| Locale | Your timezone, keyboard, and language |
| SSH | Enabled |
| Raspberry Pi Connect | Enabled/linked if Imager offers it |

Write the card, insert it into the Pi, and power on.

## 2. Open A Shell On The Pi

Wait a minute or two after first boot.

Preferred method: open Raspberry Pi Connect in your browser and press **Connect** for the device. This gives you a remote shell without needing to know the Pi IP address first.

Fallback on the same network:

```bash
ssh pi@invisible-key.local
```

If that does not work, find the Pi in your router page and SSH to its IP:

```bash
ssh pi@<pi-ip>
```

## 3. Install Basic Packages

Run this in the Pi shell:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates
```

For Raspberry Pi Connect shell access after reboots, enable lingering:

```bash
loginctl enable-linger
```

## 4. Keep The Pi Awake

Raspberry Pi OS Lite normally does not sleep like a laptop. Invisible Key controls door access, so it should run 24/7; the commands below are optional hardening if you want to defensively disable Linux sleep/suspend targets.

You can skip this step while testing. To check whether the Pi has actually suspended since boot, run:

```bash
journalctl -b | grep -Ei "PM: suspend|suspend entry|suspend exit|Starting System Suspend|Reached target.*suspend|hibernate|hybrid-sleep"
```

If that only shows skipped `systemd-hibernate-clear.service` messages, the Pi has not suspended.

Optional hardening:

```bash
sudo raspi-config nonint do_blanking 1
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

Optional boot-speed tweak, unrelated to sleep:

```bash
sudo systemctl disable NetworkManager-wait-online.service
```

## 5. Install Docker

### Raspberry Pi 3/4/5

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
sudo reboot
```

### Raspberry Pi 2 B

Use Raspberry Pi OS packages instead of Docker's upstream convenience script:

```bash
sudo rm -f /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
sudo reboot
```

After reboot, reconnect and check:

```bash
docker --version
docker compose version
```

If `docker compose` is unavailable but `docker-compose` works, use `docker-compose` in the commands below.

## 6. Install Invisible Key

```bash
git clone https://github.com/benitocalcanho/invisible-key.git
cd invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d
```

The first pull can take several minutes, especially on a Raspberry Pi 2 B.

## 7. Open The Admin Dashboard

Print the local dashboard URL:

```bash
printf 'Open this on your computer while on the same network: http://%s:5000\n' "$(hostname -I | awk '{print $1}')"
```

Open the printed URL in your browser.

Default login:

```text
admin / admin12345
```

Change the admin password immediately.

The local IP is mainly for first setup and troubleshooting. After ngrok is configured, use the ngrok URL as your normal admin URL too.

## 8. Configure The Dashboard

Now follow [First Admin Dashboard Setup](ADMIN_DASHBOARD_SETUP.md).

That guide covers:

- creating your master user
- ngrok public URL
- Google Calendar iCal sync
- Gmail SMTP email alerts
- WiFi networks
- door images and phone previews
- final testing

## 9. Optional But Recommended: Tailscale

Tailscale gives you a private admin IP for SSH and dashboard access. It can substitute Raspberry Pi Connect for shell recovery and helps if ngrok has a problem.

Create a free account at [tailscale.com](https://tailscale.com), then run:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Open the sign-in URL printed by the command. In the Tailscale dashboard, disable key expiry for the Pi so it does not require re-authentication later.

## 10. Basic Checks

Check the app:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=100 app
```

Restart the app:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml restart app
```

Update later:

```bash
cd ~/invisible-key
git pull --ff-only origin main
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml pull app
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d --force-recreate app
```

More detailed update steps are in [DEPLOY_PI.md](DEPLOY_PI.md).

## 11. WiFi And Repeater Note

Seed the primary WiFi during SD-card creation. Add or remove later networks from **Admin Dashboard -> WLAN/WiFi Networks**.

If the Pi connects through a WiFi repeater/range extender and local SSH or `http://<pi-ip>:5000` fails while ping works, disable WiFi MAC randomization on the Pi. See [Raspberry Pi 2 B Notes](INSTALL_PI2B.md#wifi-and-repeater-notes). The same fix can apply to Pi 3/4/5 behind some repeaters.

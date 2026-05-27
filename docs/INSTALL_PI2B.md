# Raspberry Pi 2 B Notes

Use [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md) for the main install walkthrough. This file only contains Raspberry Pi 2 B-specific notes.

## What Is Different On Pi 2 B

- Use **Raspberry Pi OS Lite 32-bit**.
- Raspberry Pi 2 B has no onboard WiFi; use Ethernet or a supported USB WiFi adapter.
- Docker image pulls and first startup are slower than on Pi 3/4/5.
- Do not build the Docker image locally on the Pi 2 B; pull the prebuilt GHCR image.
- Use a reliable 5V / 2A or better power supply.
- Use a good 16 GB or larger microSD card.

The app is still intended to run 24/7 on Pi 2 B. Disable WiFi power saving during setup; this is especially important with USB WiFi adapters. Raspberry Pi OS Lite normally stays awake, but see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md#5-keep-the-pi-awake) for optional sleep-target hardening and checks.

## OS Selection

In Raspberry Pi Imager:

| Field | Value |
|---|---|
| Device | Raspberry Pi 2 |
| OS | Raspberry Pi OS Lite 32-bit |
| Hostname | `invisible-key` |
| WiFi | Configure if using a USB WiFi adapter |
| SSH | Enabled |

Do not choose the 64-bit image for Raspberry Pi 2 B.

## Docker Install On Pi 2 B

On Raspberry Pi OS Lite 32-bit Trixie, Docker's upstream Raspbian repository may not provide a `trixie` release. Use Raspberry Pi OS packages:

```bash
sudo rm -f /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
sudo reboot
```

After reboot:

```bash
docker --version
docker compose version
```

If `docker compose` is unavailable but `docker-compose` works, replace `docker compose` with `docker-compose` in commands.

## App Install Command

Use the same Raspberry Pi compose command as every other Pi:

```bash
git clone https://github.com/benitocalcanho/invisible-key.git
cd invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d
```

The published Docker image includes `linux/arm/v7`, which is the architecture used by Raspberry Pi 2 B with Raspberry Pi OS Lite 32-bit.

## Performance Expectations

Normal on Pi 2 B:

- Docker image pulls can take several minutes.
- First startup can feel slow.
- The first pull after dependency changes may download a large changed layer.
- Admin dashboard actions can be slower than on a Pi 3/4/5.

Not normal:

- The Pi disappearing from the network.
- SSH timing out while ping works.
- Repeated undervoltage warnings.
- SD card errors in `dmesg`.

## WiFi And Repeater Notes

Raspberry Pi 2 B has no onboard WiFi. If using WiFi, use a supported USB WiFi adapter and seed the primary WiFi during SD-card creation. Ethernet is useful for recovery but not required for production.

Disable WiFi power saving before relying on WiFi in production:

```bash
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/wifi-powersave-off.conf >/dev/null <<'EOF'
[connection]
wifi.powersave = 2
EOF

sudo systemctl restart NetworkManager
```

Reconnect the saved network if needed and verify:

```bash
nmcli connection show
sudo nmcli connection up "<saved-wifi-name>"
iw dev wlan0 get power_save
iw dev wlan0 link
ip addr show wlan0
```

The expected result is `Power save: off`. If the Pi is powered on but disappears from WiFi, check this first.

If you use a WiFi range extender/repeater, local inbound access such as SSH or `http://<pi-ip>:5000` can fail even when ping works. Some repeaters, including basic TP-Link RE models such as TL-WA850RE, use MAC proxy/translation.

Disable NetworkManager WiFi MAC randomization on the Pi before relying on a repeater path:

```bash
sudo mkdir -p /etc/NetworkManager/conf.d
sudo nano /etc/NetworkManager/conf.d/00-disable-wifi-randomization.conf
```

Add:

```ini
[device]
wifi.scan-rand-mac-address=no

[connection]
wifi.cloned-mac-address=permanent
ethernet.cloned-mac-address=permanent
```

Reboot:

```bash
sudo reboot
```

After reconnecting, verify:

```bash
hostname -I
iw dev wlan0 link
ip addr show wlan0
ssh pi@<pi-ip>
curl -I http://<pi-ip>:5000
```

For repeaters, also check that:

- repeater DHCP server is disabled
- access control/blacklist is disabled
- firmware is current
- the main router reserves the IP against the MAC address it actually sees

If the main router shows a different MAC address for the Pi than `ip addr show wlan0`, that can be normal repeater proxy behavior.

## Troubleshooting

### Docker install fails with `trixie Release` missing

If you accidentally ran Docker's convenience script and saw:

```text
E: The repository 'https://download.docker.com/linux/raspbian trixie Release' does not have a Release file.
```

remove the broken Docker source and use Raspberry Pi OS packages:

```bash
sudo rm -f /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
sudo reboot
```

### Locale warnings during `apt`

Warnings such as `Setting locale failed` are not fatal. They usually mean the language/locale selected in Raspberry Pi Imager was not generated fully yet.

### SSH host key changed

If you reused an IP address from an older Pi install, SSH may warn that the remote host identification changed. For a freshly imaged Pi on your own network, remove the old key:

```bash
ssh-keygen -f "$HOME/.ssh/known_hosts" -R "<pi-ip>"
```

Then connect again and accept the new fingerprint.

## Quick Checks

```bash
docker --version
docker compose version
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

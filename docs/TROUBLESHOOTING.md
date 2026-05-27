# Troubleshooting And Emergency Access

Use this page when the Pi is powered on but the normal web app path is unavailable, slow, or stuck.

## Emergency Door Unlock From SSH

This fallback is for emergencies where the Pi is reachable by SSH, Raspberry Pi Connect, or Tailscale, but the web app/ngrok/browser path is not usable.

The emergency scripts run directly on the Raspberry Pi host, outside Docker. They bypass the app, so they do not create button-history entries and do not send email notifications.

Relay defaults:

| Door | BCM GPIO | Physical pin | Script |
|---|---:|---:|---|
| Building / street door | 17 | 11 | `bash open-building` |
| Apartment door | 27 | 13 | `bash open-apartment` |

The relay board is active-low. The scripts below activate the relay for 5 seconds, then force it off.

### Create The Emergency Scripts

Run this once on the Pi:

```bash
cat > ~/open-building <<'SH'
#!/usr/bin/env bash
python3 - <<'PY'
import time
from gpiozero import LED

relay = LED(17, active_high=False, initial_value=False)
try:
    print("Unlocking building door for 5 seconds...")
    relay.on()
    time.sleep(5)
finally:
    relay.off()
    relay.close()
    print("Building relay OFF.")
PY
SH

cat > ~/open-apartment <<'SH'
#!/usr/bin/env bash
python3 - <<'PY'
import time
from gpiozero import LED

relay = LED(27, active_high=False, initial_value=False)
try:
    print("Unlocking apartment door for 5 seconds...")
    relay.on()
    time.sleep(5)
finally:
    relay.off()
    relay.close()
    print("Apartment relay OFF.")
PY
SH

chmod +x ~/open-building ~/open-apartment
```

Check that host Python can import gpiozero:

```bash
python3 - <<'PY'
from gpiozero import LED
print("gpiozero host install works")
PY
```

If that fails, install the host package:

```bash
sudo apt update
sudo apt install -y python3-gpiozero
```

### Use The Scripts

After SSH login, you normally start in `/home/pi`, so no `~` or long path is needed:

```bash
bash open-building
```

```bash
bash open-apartment
```

These names are intentionally descriptive. Avoid ultra-short commands such as `ob` or `oa`; they are too easy to run accidentally.

### If You See `GPIO busy`

If the app container is still running, it may already own GPIO17/GPIO27. Modern Raspberry Pi GPIO access through `lgpio` is strict and can return:

```text
lgpio.error: 'GPIO busy'
```

That is expected. Two processes should not drive the same relay pin at the same time. Stop the app, unlock, then start it again:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml stop app
bash ~/open-building
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml start app
```

For the apartment door:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml stop app
bash ~/open-apartment
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml start app
```

If Docker is hung but the Pi shell works, try restarting Docker before starting the app again:

```bash
sudo systemctl restart docker
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml up -d
```

## Quick Health Checks

Run these on the Pi, not on your laptop:

```bash
uptime
hostname -I
nmcli device status
iw dev wlan0 link
iw dev wlan0 get power_save
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml ps
df -h
journalctl -p warning..alert --since "24 hours ago"
```

Expected signs of health:

- `wlan0` is connected
- `Power save: off`
- the `invisible-key` container is `Up`
- disk usage is comfortably below 80%
- no repeated WiFi disconnect, undervoltage, filesystem, or Docker errors

## WiFi Reconnect Check

If the Pi is powered on but not reachable over WiFi, check from a recovery shell over LAN, Raspberry Pi Connect, or Tailscale:

```bash
nmcli device status
nmcli device wifi list
nmcli connection show
iw dev wlan0 get power_save
iw dev wlan0 link
journalctl -u NetworkManager --since "24 hours ago" | grep -Ei "wlan0|disconnect|failed|deauth|activated|power|dhcp|timeout"
```

Reconnect a saved network manually:

```bash
sudo nmcli connection up "<saved-wifi-name>"
```

If power saving is not off, fix it as described in [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md#4-disable-wifi-power-saving).

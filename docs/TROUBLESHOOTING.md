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

## Unlock Button Animated But Door Did Not Unlock

Current production builds only show the guest unlock animation after the GPIO pulse API returns success. If a user reports an animation without a relay click, check both access logs and audit logs before changing code or wiring.

Recent app log check:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml logs --tail=300 app \
  | grep -aEi "GPIO pulse|POST /api/gpio|button_press|401|403|500|failed|exception"
```

Recent audit events:

```bash
cd ~/invisible-key
docker compose -f docker-compose.prod.yml -f docker-compose.pi.yml exec -T app python - <<'PY'
import sqlite3

db = "/app/backend/instance/data/invisible_key.db"
con = sqlite3.connect(db)

for row in con.execute("""
    select id, event, detail, timestamp
    from audit_logs
    where event in ('button_press', 'gpio_pulse_started', 'gpio_pulse_ended')
    order by id desc
    limit 40
"""):
    print(row)
PY
```

Interpretation:

- No `button_press` and no `POST /api/gpio` means the browser/request did not reach the backend.
- `POST /api/gpio/.../pulse` with `401` or `403` means auth/session/access denied.
- `GPIO pulse start requested`, `GPIO pulse accepted`, and `GPIO pulse ended` means the backend drove the pin path successfully; check relay power, wiring, and lock hardware.
- `GPIO pulse failed` or stack traces indicate a backend/GPIO driver problem.

Also check Pi power and kernel warnings around the event time:

```bash
journalctl -p warning..alert --since "30 minutes ago" --no-pager
dmesg -T | grep -Ei "gpio|lgpio|voltage|under-voltage|thrott|usb|brcm|error|warn" | tail -80
vcgencmd get_throttled
```

## Production Update Script

Production runs from the Docker image, not from `python app.py` on the Pi. Use:

```bash
cd ~/invisible-key
./scripts/update-production.sh
```

If GitHub Actions is still building, this script may pull the previous image. Wait for the action to finish, then run it again.

Do not use old local rebuild scripts that run `npm run build`, `pkill -f "python app.py"`, or `python app.py` for production. Replace any old script with a guard:

```bash
cd ~/invisible-key
cat > rebuild_and_restart.sh <<'SH'
#!/usr/bin/env bash
echo "This script is obsolete for production."
echo "Use: ./scripts/update-production.sh"
exit 1
SH
chmod +x rebuild_and_restart.sh
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

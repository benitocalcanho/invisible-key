# Remote Access — Raspberry Pi Connect + ngrok + Tailscale

## Shared Behavior Note

Remote access configuration is host-specific, but calendar scheduling remains deployment-local timezone based.
Avoid maintainer-specific timezone assumptions in remote operations and support flows.

## Architecture

Invisible Key uses three free remote-access services, in this order:

| Order | Channel | Who | Purpose |
|---:|---|---|---|
| 1 | **Raspberry Pi Connect** | Admin | Free browser shell for first setup and maintenance |
| 2 | **ngrok** | Admin + guests | Free public HTTPS URL for the app |
| 3 | **Tailscale** | Admin | Free private IP for SSH/shell and admin-only dashboard access |

No paid subscription is required for the normal Invisible Key setup. This is a fundamental advantage of the app: it works with almost any internet connection, including CGNAT/mobile/repeater-style networks, without router configuration, port forwarding, or a private domain. Guest access, admin access, and recovery access can all work for free.

Use Raspberry Pi Connect first to install and recover the Pi. Use ngrok as the normal URL for both guests and admins. Add Tailscale as an optional but recommended private admin path.

---

## Raspberry Pi Connect (Admin Shell)

Raspberry Pi Connect is free and provides remote shell access through a browser without router port forwarding. During first boot, use the **Connect** button on the Raspberry Pi Connect website to open a shell without needing to know the Pi IP address. It is also a good replacement for Tailscale when you only need occasional admin/recovery shell access to the Pi.

Set it up during Raspberry Pi Imager if the option is available:

1. Choose Raspberry Pi OS Lite.
2. Open OS Customisation.
3. Configure hostname, user/password, WiFi, locale, and SSH.
4. Enable/link Raspberry Pi Connect.

On headless Raspberry Pi OS Lite, enable user lingering so Connect can remain reachable after reboot before an interactive login:

```bash
loginctl enable-linger
```

Use Raspberry Pi Connect for:
- first installation before you know the Pi IP address
- checking Docker logs
- pulling app updates
- restarting the container
- fixing WiFi/ngrok/app settings when you are not on the local network

To print the first local dashboard URL from a Connect shell:

```bash
printf 'Open this on your computer while on the same network: http://%s:5000\n' "$(hostname -I | awk '{print $1}')"
```

Raspberry Pi Connect does not expose the web app to guests. Keep ngrok for guest/admin web access after setup.

---

## ngrok (User Access)

### What is ngrok?
ngrok creates an HTTPS tunnel from the public internet to your Flask app running locally
on the Pi. Its free tier is enough for the normal Invisible Key setup: one public app URL for both guests and admins.

### Setup

1. Create a free account at [ngrok.com](https://ngrok.com)
2. Get your auth token: Dashboard → Getting Started → Your Authtoken
3. (Recommended) Reserve a free static domain: Dashboard → Cloud Edge → Domains → New Domain
4. Paste your token (and optionally the static domain) in:
   **Admin Dashboard → ngrok Tunnel** tab → Save

The tunnel starts automatically and restarts on save. No app restart needed.

### How it works

When the Flask app starts, it automatically:
1. Authenticates with ngrok using your token
2. Opens an HTTPS tunnel to `localhost:5000`
3. The public URL is shown in **Admin Dashboard → Overview**

Admins and guests access:
```
https://yourname.ngrok-free.app/login
```
After ngrok is configured, use this as the normal admin URL too. Use the local `http://<pi-ip>:5000` URL mainly for same-network troubleshooting.

### Sharing URLs with Users

Send each user their access URL. Since JWT authentication is required,
even if someone guesses the URL they cannot access data without valid credentials.

### ngrok Free Tier Limits

| Feature | Free Tier |
|---------|-----------|
| Tunnels | 1 simultaneous |
| Static domain | 1 free domain |
| Bandwidth | 1 GB/month |
| Connections | Unlimited |

This is sufficient for a Raspberry Pi project with a small number of users.

---

## Tailscale (Optional, Recommended Admin Access)

### What is Tailscale?
Tailscale is a free zero-config VPN built on WireGuard for personal/admin use. It assigns your Pi a stable private
IP in the `100.x.x.x` range that is only reachable by devices in your Tailscale account.
No port forwarding or DDNS required — works behind CGNAT.

Tailscale can substitute Raspberry Pi Connect for admin shell access. It can also provide an admin-only private URL for the dashboard from devices signed into your Tailscale account. It is not intended as the normal guest URL unless you deliberately add guest devices to your Tailscale network.

### Setup

Create a free account at [tailscale.com](https://tailscale.com), then install Tailscale on the Pi with the official convenience script:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Follow the URL printed by `sudo tailscale up` in a browser on any device signed into your Tailscale account.

Check the Pi's Tailscale IP:

```bash
tailscale ip -4
```

The helper script `scripts/03-setup-tailscale.sh` runs the same installer and enables the service.

### Disable Key Expiry

After the Pi appears in the Tailscale admin dashboard, open the device details and disable key expiry for this Pi. This is important for production: if key expiry remains enabled, Tailscale may require re-authentication later and remote access can stop until someone logs the Pi back in.

### Accessing the Admin Dashboard

From **any device** in your Tailscale network:
```
http://100.x.x.x:5000
```

Tailscale is not required to access the admin dashboard; the dashboard is also accessible via ngrok after setup. Use Tailscale when you want private-network style admin access, SSH, or a recovery path independent of ngrok.

### Tailscale Access Controls (Optional ACL)

In your [Tailscale admin console](https://login.tailscale.com/admin/acls), you can
restrict which devices can reach the Pi:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["autogroup:owner"],
      "dst": ["tag:invisible-key:5000"]
    }
  ],
  "tagOwners": {
    "tag:invisible-key": ["autogroup:owner"]
  }
}
```

---

## CGNAT Compatibility

ngrok, Raspberry Pi Connect, and Tailscale work without router configuration:
- no port forwarding required
- no public IP required
- no private domain required
- suitable for mobile networks, CGNAT ISPs, repeaters, and most normal home internet connections
- free for the normal Invisible Key setup

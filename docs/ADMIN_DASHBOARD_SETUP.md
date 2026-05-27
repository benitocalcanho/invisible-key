# First Admin Dashboard Setup

This guide starts after the app is running and you can open the admin dashboard.

Default login:

```text
admin / admin12345
```

Change the admin password first. Then configure the dashboard in this order.

## 1. Create Your Master User

A **master** user can always unlock the doors. It is not controlled by the calendar.

1. Open **Admin Dashboard -> Users**.
2. Click **New user**.
3. Enter your username and password.
4. Choose role **Master**.
5. Click **Create**.
6. Log out and test logging in as the master user.

Keep the admin account for configuration. Use the master account for normal door access.

## 2. Configure ngrok

ngrok gives you the normal web URL for both guests and admins.

1. Create a free account at [ngrok.com](https://ngrok.com).
2. In the ngrok dashboard, copy your auth token.
3. Optional but recommended: reserve a free static domain.
4. In Invisible Key, open **Admin Dashboard -> ngrok Tunnel**.
5. Paste:

| Field | Value |
|---|---|
| Auth Token | Your ngrok auth token |
| Static Domain | Your reserved domain, if you have one |

6. Click **Save**.
7. Wait a few seconds. The ngrok URL should appear at the top of the admin dashboard.
8. From now on, use the ngrok URL as your normal admin URL.

Example:

```text
https://your-name.ngrok-free.app/login
```

The local Pi URL is still useful for troubleshooting on the same network.

## 3. Configure Google Calendar iCal

Use this if you have a normal free Gmail/Google account.

Invisible Key does not need Google API keys, OAuth, or a service account. It only needs the private iCal link from your calendar.

### Get The iCal Link

1. On a computer, open [calendar.google.com](https://calendar.google.com).
2. On the left, find the calendar you use for bookings.
3. Click the three dots next to that calendar.
4. Click **Settings and sharing**.
5. Scroll down to **Integrate calendar**.
6. Find **Secret address in iCal format**.
7. Copy the link. It usually starts with:

```text
https://calendar.google.com/calendar/ical/...
```

Keep this link private. Anyone with this link can read the calendar feed. If you ever leak it, use Google's **Reset** option to create a new secret address.

### Paste It In Invisible Key

1. Open **Admin Dashboard -> Calendar Sync**.
2. In **Google Calendar (iCal)**, paste the private iCal URL.
3. Click **Save**.
4. Set **Guest Password Source**:

| Mode | What it means |
|---|---|
| Fixed password | Every calendar guest gets the same password you type in the dashboard. |
| Last word of event title | The last word of the calendar event title becomes the guest password. Useful for phone-number endings, like `Alice 0612`. |

5. Set check-out and check-in times. Defaults are usually correct:

| Field | Typical value |
|---|---|
| Check-out time | `12:00` |
| Check-in time | `14:00` |

6. Configure the cleaner account in **Cleaner Account**.
7. Click **Save** for each changed section.
8. Click **Apply Schedule Changes** after changing check-in/check-out times.
9. Click **Sync Now** once to test.

### Calendar Event Example

If a guest stays from May 1 and checks out at noon on May 4, create an all-day Google Calendar event from May 1 through May 3.

Example title using last-word password mode:

```text
Alice 0612
```

Invisible Key will create:

| Field | Result |
|---|---|
| Username | `alice` |
| Password | `0612` |
| Guest access starts | check-in time, e.g. 14:00 |
| Guest access ends | check-out time, e.g. 12:00 on checkout day |

## 4. Configure Gmail Email Notifications

Email notifications are optional. They let you receive an email when someone presses a door button.

For a free Gmail account, do **not** use your normal Gmail password. Use a Google App Password.

### Create A Google App Password

1. Open [myaccount.google.com](https://myaccount.google.com).
2. Go to **Security**.
3. Turn on **2-Step Verification** if it is not already enabled.
4. Open [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
5. Sign in if Google asks.
6. Create an app password. Use a name like:

```text
Invisible Key
```

7. Google will show a 16-character password.
8. Copy it immediately.

Use this app password only for Invisible Key. Do not paste your normal Gmail password into the app.

If you cannot find App Passwords, check that 2-Step Verification is enabled. Some Google accounts, such as managed school/company accounts or accounts using Advanced Protection, may not allow app passwords.

### Paste Gmail SMTP Settings In Invisible Key

Open **Admin Dashboard -> E-Mail** and enter:

| Field | Gmail value |
|---|---|
| SMTP Host | `smtp.gmail.com` |
| SMTP Port | `587` |
| SMTP Username | your full Gmail address, e.g. `yourname@gmail.com` |
| SMTP Password | the 16-character Google app password |
| Sender Email | your full Gmail address, e.g. `yourname@gmail.com` |
| Recipient Email | where alerts should arrive, often the same Gmail address |

Click **Save**.

Then test by pressing a door button with a master user. You should receive an email saying which user pressed which button.

## 5. Configure WiFi Networks

Use this when the Pi may be moved to another apartment or network.

1. Open **Admin Dashboard -> WLAN/WiFi Networks**.
2. Scan nearby networks or manually enter the SSID.
3. Enter the WiFi password.
4. Save the credentials.

The Pi will connect automatically when that network is available. The operating system should already have WiFi power saving disabled from the Raspberry Pi setup guide; if the Pi later disappears from WiFi while still powered on, re-check `iw dev wlan0 get power_save`.

## 6. Upload Door Images

1. Open **Admin Dashboard -> Door Images**.
2. Upload the building door photo.
3. Upload the apartment door photo.
4. Adjust horizontal position, vertical position, and zoom.
5. Use the phone preview buttons to check that the unlock button does not cover important parts of the image.
6. Click **Save Position**.

## 7. Final Test

Before giving the link to guests:

1. Log in as admin and confirm the dashboard loads.
2. Log in as master and press both door buttons.
3. Check **Button History** for the button press.
4. Check **Door Log** if a reed sensor is installed.
5. Open the ngrok URL from your phone on mobile data.
6. Run **Calendar Sync -> Sync Now** and confirm the result message makes sense.

When all of that works, the app is ready for production.

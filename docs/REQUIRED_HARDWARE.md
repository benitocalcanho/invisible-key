# Required Hardware

This is the hardware used for a typical Invisible Key installation with one building/intercom relay and one apartment-door relay.

Read [HARDWARE.md](HARDWARE.md) and [INTERCOM.md](INTERCOM.md) before wiring.

## Core Electronics

| Item | Purpose | Notes |
|---|---|---|
| Raspberry Pi | Runs Invisible Key | Raspberry Pi 2/3/4/5 class boards are suitable. Raspberry Pi Zero W v1.1 is not recommended for the Docker image. |
| MicroSD card | Raspberry Pi OS and app storage | Use a reliable card; 16 GB minimum, 32 GB or larger recommended. |
| Raspberry Pi power supply | Stable Pi power | Minimum 2A. Use a quality 5V supply; underpowered supplies can corrupt the SD card. |
| 5V 2-channel relay board | Switches building and apartment unlock circuits | Relay IN1 is used for the building/intercom unlock. Relay IN2 is used for the apartment opener. |
| Jumper wires | Raspberry Pi GPIO to relay board | Female-to-female Dupont jumpers are usually easiest for the Pi header and relay inputs. |

## Door And Opener Hardware

| Item | Purpose | Notes |
|---|---|---|
| 230/240V AC to 12V AC power adapter | Power source for the apartment opener/buzzer circuit | Use only a properly enclosed, rated adapter. Mains wiring must be done safely and legally. |
| 12V AC electric door opener set | Opens the apartment door | Required for the apartment-door relay path. The apartment door must be compatible with an electric opener/strike. |
| Existing intercom with door-release button | Building/street door unlock | Relay 1 is wired across the intercom door-release button or a confirmed equivalent contact pair. |

## Wiring Material

| Item | Purpose | Notes |
|---|---|---|
| 6-core telephone cable, 0.6 mm | Low-voltage wiring between Pi/relay/intercom/opener circuits | German: `6-ader Telefonkabel 0,6 mm`. Useful because one cable can carry several relay/control lines cleanly. |
| Small insulated screw terminals or connectors | Join low-voltage wires cleanly | Use suitable connectors for the cable gauge and voltage. |
| Heat-shrink tubing or insulation tape | Insulates solder joints and exposed contacts | Prevents accidental shorts inside the intercom or relay enclosure. |
| Enclosure or mounting box | Protects the Pi, relay board, and wiring | Keep mains-voltage parts physically separated from Raspberry Pi and relay input wiring. |

## Optional But Useful

| Item | Purpose | Notes |
|---|---|---|
| Multimeter | Confirms voltages and contact pairs | Use before connecting the relay outputs. |
| Reed sensor | Door open/closed logging | Optional; connects to GPIO23 and GND. |
| Tailscale | Private admin/SSH recovery path | Software, not hardware, but strongly recommended for headless operation. |

## Compatibility Disclaimer

Invisible Key only closes relay contacts. It is designed for doors that already have an electric opener, electric strike, or intercom door-release circuit. It does not turn a key, move a manual deadbolt, pull a handle, or replace a motorized smart lock.

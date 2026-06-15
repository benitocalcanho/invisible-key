# Intercom Wiring

This note documents the actual relay wiring used for Invisible Key.

Use [REQUIRED_HARDWARE.md](REQUIRED_HARDWARE.md) for the parts list before buying or wiring components.

## Door Compatibility Disclaimer

Invisible Key is designed for installations where the door already has an electric opener, electric strike, or intercom door-release circuit. It only closes relay contacts for a few seconds.

For the apartment door, this wiring fits doors that can be opened electrically from the outside once the opener is energized. This is common in Germany, Switzerland, the UK, and some other buildings. If the door is locked by a manual key-turned deadbolt, or if someone must turn a handle from outside, this relay wiring is not enough by itself.

## Raspberry Pi To Relay Board

The relay module is powered from the Raspberry Pi 5V header pins. Physical pins 2 and 4 are both 5V; this installation uses physical pin 4 because it sits next to physical pin 6 / GND.

| Relay board terminal | Raspberry Pi physical pin | BCM GPIO | Purpose |
|---|---:|---:|---|
| VCC | 4 | 5V | Relay board power |
| GND | 6 | GND | Relay board ground |
| IN1 | 11 | GPIO17 | Building / intercom unlock relay |
| IN2 | 13 | GPIO27 | Apartment electric opener relay |

Do not connect Raspberry Pi GPIO pins directly to the intercom or the 12V AC opener circuit. The Pi only controls the relay input side.

## Relay 1: Building Intercom

Relay IN1 is controlled by GPIO17 and is used for the building / street door.

On the intercom, solder the relay output contacts across the two contacts behind the button that unlocks the building door:

```text
Intercom unlock button contact A -> relay 1 COM
Intercom unlock button contact B -> relay 1 NO
```

When the relay is off, the intercom button circuit stays open. When Invisible Key pulses GPIO17, relay 1 closes briefly and the intercom sees the unlock button being pressed.

### Ritto TwinBus 7630 Edge Connector Note

For a Ritto TwinBus 7630, the building-door opener can also be triggered at the bottom PCB edge connector, next to the physical door-opener button.

The PCB has two edge connectors:

- top edge connector: 3 contacts, separated by a slit
- bottom edge connector: 7 contacts in one row, next to the physical door-opener button

This guide uses local numbering for the bottom 7-contact connector. Viewed from the component side, count from left to right, with the physical door-opener button immediately to the right of contact 7:

```text
bottom edge connector:

1 2 3 4 5 6 7  [door-opener button]
```

Wire relay 1 across local contacts 3 and 4:

```text
Bottom edge local contact 3 -> relay 1 COM
Bottom edge local contact 4 -> relay 1 NO
```

When Invisible Key pulses GPIO17, relay 1 briefly shorts local contacts 3 and 4, equivalent to pressing the intercom door-opener button.

Using a 3-pin edge-card connector avoids soldering directly to the intercom PCB:

```text
Steckkartenverbinder 3-polig
Kartenstecker
Lumberg 2,5 R /03
RM 2.54 mm
```

External references may number these contacts differently because they count other PCB contacts as well. For this guide, the important reference is the bottom 7-contact connector: count from the left, with the door-opener button immediately to the right of contact 7.

Credit/reference for the Ritto TwinBus edge-connector approach:

- https://keilerkonzept.com/blog/ritto/
- https://www.deh0511.de/twinbus/

Confirm the contact numbering on your exact intercom revision before wiring.

## Relay 2: Apartment Electric Opener

Relay IN2 is controlled by GPIO27 and is used for the apartment door opener.

Relay 2 switches the 12V AC supply for the apartment electric door opener:

```text
12V AC supply / opener circuit -> relay 2 COM/NO
```

Use the relay output side only for the 12V AC circuit. Confirm the relay module is rated for the opener voltage and current.

## Safety Checks

Before soldering or connecting the relay outputs:

1. Confirm with a multimeter that the intercom unlock button contacts are low voltage.
2. Confirm that briefly shorting the two intercom unlock contacts opens the building door.
3. Confirm the apartment opener uses 12V AC and that the relay rating is sufficient.
4. Power off circuits before soldering or moving wires where possible.
5. Insulate solder joints and screw-terminal wiring so they cannot touch nearby contacts.

## Test

After wiring, log in as a master user and press both app buttons:

| App button | Expected action |
|---|---|
| Building door | Relay 1 clicks and the intercom unlocks the building door |
| Apartment door | Relay 2 clicks and the 12V AC apartment opener activates |

If the app is unavailable but SSH works, use the emergency scripts in [TROUBLESHOOTING.md](TROUBLESHOOTING.md#emergency-door-unlock-from-ssh).

# SP661E (BanlanX) BLE protocol notes

Reverse-engineered from a single-colour SP661E PWM controller (firmware string `V1.0.02`).
Everything marked **verified** was confirmed on the device (state read-back and/or visually on the
LED strip). Everything else is a hypothesis.

## 1. Device and BLE layout

| Item | Value |
|---|---|
| Advertised name | `LMB` |
| Manufacturer data | company id `0x5053` ("SP"), payload `01 00 <MAC tail> 00 00 00` (ends in `62 d3 ea` for the unit tested) |
| Advertised service | `0xE0FF` |
| Control service | `0000ffe0-0000-1000-8000-00805f9b34fb` |
| Control characteristic | `0000ffe1-...` (write, write-without-response, notify) |
| OTA service | `5833ff01-9b8b-5191-6142-22a4536ef123`: **never write to it** (firmware update channel) |

Only one BLE connection is accepted at a time (phone app *or* host, not both). The controller does
not push state on its own: enable notifications on FFE1 and send a state query.

Before the dedicated `SP661E` model existed, UniLED matched this device by manufacturer-data
byte `0x01` and treated it as an SP601E (SPI controller), which sends `AA 2F 00`; the SP661E
ignores that, so setup failed with `device update failed`. The SP661E speaks the "6xx" framing
(below) but with a different state layout and different command payloads than the SP63xE code.

Note: the controller only answers a state query that is written **without response**
(`write_without_response`). A write with response is accepted but never answered.

## 2. Frame format

```
53 CMD 00 01 00 LEN DATA[LEN]
```

`53` header, `CMD` command, `00` key (unencrypted), `01 00` constant, `LEN` payload length.
Responses use the same framing on FFE1 notifications. Write without response works.

## 3. Commands (all verified)

All control commands take a payload that starts with `01` (channel 1).

| Action | Frame | Notes |
|---|---|---|
| Query state | `53 02 00 01 00 01 01` | reply is `53 02 ...`, 98-108 bytes |
| Power on | `53 50 00 01 00 02 01 01` | |
| Power off | `53 50 00 01 00 02 01 00` | |
| Brightness | `53 51 00 01 00 03 01 80 LL` | `LL` 0-255, linear (remote steps: 10%=`1a`, 20%=`33`, 30%=`4d`, 50%=`80`, 80%=`cc`, 100%=`ff`) |
| Secondary level | `53 51 00 01 00 03 01 00 LL` | sets state byte `[50]`; no visible effect identified |
| Mode / effect | `53 53 00 01 00 03 01 MM EE` | see section 4 |
| Effect speed | `53 54 00 01 00 02 01 SS` | `SS` 00-0a accepted; `80` ignored; higher is faster |

Pitfall: a two-byte brightness payload (`01 LL`) sets the level to 0 (strip drops to minimum). The
level is always the **last** byte, and the byte before it selects the field (`80` = brightness).

## 4. Modes

| `MM` | `EE` | Result |
|---|---|---|
| `02` | `01` | solid colour (default mode) |
| `04` | `01` | triangle (smooth ramp) |
| `04` | `02` | strobe |
| `04` | `03` | heartbeat |
| `06` | `01` | music mode: selectable, but no reaction to sound; the unit has no microphone, so audio is probably streamed by the phone app (not investigated) |

Effects 01-03 were identified visually in the order the RF remote cycles them.

## 5. State reply layout (offsets in the full notification, header included)

| Offset | Meaning |
|---|---|
| `[5]` | payload length (`0x62` normal; changes if the device changes internal mode) |
| `[13..19]` | firmware string (`V1.0.02`) |
| `[44]` | power (`01` on, `00` off) |
| `[47]` | mode (`02` solid, `04` dynamic, `06` music) |
| `[48]` | effect number |
| `[50]` | secondary level |
| `[51]` | brightness 0-255 (in animated modes this is the *current output* and oscillates, so do not treat it as the setting) |
| `[57]` | effect speed |

Other bytes were not decoded. Offsets differ from UniLED's SP63xE parser (e.g. power is `[44]`, not
`[29]`).

## 6. Dangerous / unexplored commands

Found while probing with a blind sweep. They modify device configuration, so avoid them:

- `0x5E` rewrites about 40 state bytes at once (looks like a reset). After it the RF remote lost
  its pairing and had to be re-paired.
- `0x08`, `0x0A`, `0x0B`, `0x0D`, `0x17`, `0x30`, `0x57`, `0x58`, `0x59`, `0x5A` each change an
  unidentified setting or flag. `0x6A`/`0x6B` (light type, channel order in related models) were
  deliberately never sent.
- Sending an arbitrary mode number to `0x53` (for example `80`) leaves the device in an undefined mode.

The RF remote can be re-paired by powering the controller on and long-pressing ON on the remote
within about 20 s (documented for sibling BanlanX models, not checked against an SP661E manual).

## 7. Not investigated

- Timers (the RF remote has a 15/30/45/0 timer button, but pressing it produced no state change).
- Music mode audio input.
- RGB/CCT variants: this unit is single-colour only.
- Packet capture of the BanlanX app (would settle the remaining unknowns).

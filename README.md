<div align="center">
  <img src="assets/banner.svg?v=2" alt="PixMob Wave2 — Flipper Zero RF Controller · 868.415 MHz · Sub-GHz · Group 0" width="820">
</div>

<div align="center">

# PixMob Wave2 for Flipper Zero

Ready-to-use Sub-GHz files that wake, color, and switch off a **PixMob Wave2 /
Waveband 2** RF LED wristband using the Flipper Zero's built-in radio.

[![Release](https://img.shields.io/github/v/release/weeknds/pixmob-wave2-flipper-zero?display_name=tag&label=release&color=16a866)](https://github.com/weeknds/pixmob-wave2-flipper-zero/releases/latest)
[![Tests](https://github.com/weeknds/pixmob-wave2-flipper-zero/actions/workflows/validate.yml/badge.svg)](https://github.com/weeknds/pixmob-wave2-flipper-zero/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a866)](LICENSE)
![RF: 868.415 MHz](https://img.shields.io/badge/RF-868.415%20MHz-39ff88)

**[Download the files](https://github.com/weeknds/pixmob-wave2-flipper-zero/releases/latest/download/PixMob_Wave2_G0.zip)**
 · [Project website](https://weeknds.github.io/pixmob-wave2-flipper-zero/)
 · [RF protocol](PROTOCOL.md)

</div>

**What is this?** 41 Flipper Zero `.sub` files plus a dependency-free Python
generator, for European PixMob Wave2 / Waveband 2 wristbands. You get 20
persistent colors, a persistent OFF, the required wake sequence, and quick
commands for a wristband that is already awake.

**Where do I start?** Copy `PixMob_Wave2_G0` to `/subghz/` on the SD card, open
**Sub-GHz → Saved → PixMob_Wave2_G0 → one_press**, and send `02_RED_G0.sub`.
The first command takes about 18 seconds because it carries a 16.6-second wake
sequence — that is deliberate, not Flipper lag.

> [!IMPORTANT]
> Waveband 2 is controlled by **RF, not infrared**. Open these files through
> **Sub-GHz → Saved**, never the Infrared application. This release targets the
> European 868.415 MHz hardware and transmits on group 0 with the internal
> CC1101 — no external radio module is required.

## Did PixMob IR codes do nothing for you?

Then your wristband is probably a radio model, and no infrared file will ever
reach it. PixMob makes both kinds:

| Wristband | Control medium | Use |
|---|---|---|
| Classic PixMob (dark IR window on the housing) | Infrared | An IR project such as [`danielweidman/flipper-pixmob-ir-codes`](https://github.com/danielweidman/flipper-pixmob-ir-codes), via the **Infrared** app |
| **PixMob Waveband 2, Europe** (no IR window) | Radio, **868.415 MHz** | **This repository**, via **Sub-GHz → Saved** |
| Other regional RF Wavebands | Radio, other frequencies | Not covered here — [`PROTOCOL.md`](PROTOCOL.md) is a starting point |

The quickest physical tell is that dark translucent window: an infrared
receiver needs to see through one, a radio receiver does not. Full explanation
and troubleshooting: **[Is your PixMob infrared or
RF?](https://weeknds.github.io/pixmob-wave2-flipper-zero/ir-or-rf.html)**

## Confirmed configuration

| Property | Value |
|---|---|
| Wristband | PixMob Wave2 / Waveband 2 |
| Region | Europe |
| Carrier | 868.415 MHz |
| Modulation | OOK / ASK |
| Address | Group 0 (universal group) |
| Controller | Flipper Zero internal CC1101 |
| Confirmed signal | Persistent red (`RED_G0`) |

The checked-in `RED_G0` signal is the regression reference: the generator must
recreate its corrected payload, CRC, wake sequence, and RAW timings exactly.

## Quick start

1. Download
   [`PixMob_Wave2_G0.zip`](https://github.com/weeknds/pixmob-wave2-flipper-zero/releases/latest/download/PixMob_Wave2_G0.zip).
2. Extract the `PixMob_Wave2_G0` folder.
3. Copy it to `SD Card/subghz/` using qFlipper, the mobile app, or an SD-card reader.
4. On the Flipper, open **Sub-GHz → Saved → PixMob_Wave2_G0 → one_press**.
5. Send `02_RED_G0.sub` and let the full transmission finish.
6. Once the wristband is awake, use `quick_after_wake` for near-instant changes.

Hold the Flipper close to the wristband during the first test. Fresh batteries
are strongly recommended.

## Why does the first command take about 18 seconds?

PixMob Wavebands enter a low-power sleep state. A sleeping wristband ignores an
ordinary color packet until it has received enough valid RF traffic to wake its
receiver and microcontroller.

Every file in `one_press` therefore contains the complete sequence:

```text
┌──────────────────────────────┐   ┌─────────────────────┐
│ 336 black wake frames        │ → │ 20 color/OFF frames │
│ approximately 16.6 seconds   │   │ approximately 1 sec │
└──────────────────────────────┘   └─────────────────────┘
```

This is deliberate—not Flipper lag.

After one successful `one_press` command, the wristband remains receptive for a
while. Files in `quick_after_wake` omit the long wake section and respond in
about one second. If quick commands stop working, send any `one_press` command
again.

## Included colors

Each color has a self-waking version and a quick version.

| Command | RGB | Notes |
|---|---:|---|
| OFF | `0, 0, 0` | Persistent black; turns the LEDs off |
| RED | `252, 0, 0` | Confirmed reference color |
| GREEN | `0, 252, 0` | Full green |
| BLUE | `0, 0, 252` | Full blue |
| WHITE | `252, 252, 252` | Maximum output; needs healthy batteries |
| SOFT_WHITE | `128, 128, 128` | Lower-current white |
| WARM_WHITE | `252, 160, 80` | Warm amber white |
| COOL_WHITE | `160, 200, 252` | Cool blue white |
| YELLOW | `252, 252, 0` | Red + green |
| CYAN | `0, 252, 252` | Green + blue |
| MAGENTA | `252, 0, 252` | Red + blue |
| ORANGE | `252, 80, 0` | Orange |
| GOLD | `252, 160, 0` | Gold |
| PURPLE | `128, 0, 252` | Purple |
| VIOLET | `200, 0, 252` | Violet |
| PINK | `252, 40, 128` | Pink |
| LIME | `128, 252, 0` | Lime green |
| TEAL | `0, 160, 128` | Teal |
| AQUA | `0, 252, 160` | Aqua |
| SKY_BLUE | `0, 128, 252` | Sky blue |

The RF protocol carries six bits per channel, so RGB values are quantized to
multiples of four.

## Turning the wristband off

Use:

- `one_press/01_OFF_G0.sub` if the wristband may be asleep.
- `quick_after_wake/01_OFF_G0_QUICK.sub` if it is already awake.

OFF is not a special radio command. It uses the same persistent group-0 frame
as the working colors, with red, green, and blue all set to zero.

## Repository layout

```text
.
├── subghz/
│   ├── one_press/          # wake + persistent color/OFF
│   └── quick_after_wake/   # color/OFF without the long wake sequence
├── generator/generate.py   # dependency-free signal generator
├── tests/                  # CRC, codec, timing, and file-format tests
├── docs/                   # GitHub Pages site
├── PROTOCOL.md             # RF frame and checksum documentation
└── assets/banner.svg
```

## Rebuild the Flipper files

Python 3.10 or newer is sufficient; there are no external dependencies.

```bash
python3 generator/generate.py
python3 -m unittest discover -s tests -v
```

The test suite checks known RF vectors, encode/decode round trips, the OFF
payload, transmission duration, Flipper headers, and the 512-value RAW line
limit.

## Troubleshooting

### Nothing happens

- Use a file from `one_press` and wait until transmission finishes.
- Start with `02_RED_G0.sub`; it draws less current than full white.
- Hold the Flipper close to the wristband.
- Install fresh batteries and clean the contacts.
- Confirm the Flipper is allowed to transmit at 868.415 MHz in your region.

### Red works, but another color does not

Weak coin cells can brown out under high LED current—especially maximum white.
Try `SOFT_WHITE`, a single-channel color, and fresh batteries.

### Quick commands stopped responding

The wristband returned to sleep. Send a `one_press` file again.

### My wristband uses 915 MHz

This release targets the European 868 MHz hardware. Do not change frequencies
or bypass Flipper regional restrictions unless transmission is legal where you
are located.

## How it works

Each RF message contains an 18-bit preamble/synchronization sequence and nine
line-coded payload bytes. Seven decoded 6-bit fields contain the mode, RGB,
timing, and group. A reversed CRC-12 protects the encoded body.

Older example implementations commonly mixed the two orientations of the
6b/8b table or processed the CRC in the wrong bit order. This generator uses the
on-air byte orientation and validates against known working frames. See
[PROTOCOL.md](PROTOCOL.md) for the complete packet description.

## Frequently asked questions

### Can a Flipper Zero control a PixMob Wave2 wristband?

Yes, for a compatible RF Wave2/Waveband 2. The built-in CC1101 can transmit the
868.415 MHz OOK signal using Flipper Sub-GHz RAW files.

### Should I use a `.sub` file or a `.ir` file?

Use `.sub`. PixMob Waveband products are RF-controlled. An `.ir` file drives the
Flipper infrared LED and cannot produce the required radio signal.

### Why does RED work but channel/group-specific commands fail?

Group 0 is the universal PixMob group. This project deliberately uses group 0
for every command rather than assuming how a particular event programmed its
group registers.

## Responsible use

Use this project with wristbands you own and only on frequencies permitted in
your region. Do not transmit at active events or interfere with professional
lighting systems.

## Acknowledgements

This project builds on public PixMob protocol research by
[danielweidman](https://github.com/danielweidman/pixmob-ir-reverse-engineering),
[sueppchen](https://github.com/sueppchen/PixMob_waveband), Serge-45, and the
broader PixMob reverse-engineering community. Flipper files follow the
[official Sub-GHz file format](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/SubGhzFileFormats.md).

## License

[MIT](LICENSE)

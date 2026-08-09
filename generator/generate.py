#!/usr/bin/env python3
"""Generate Flipper Zero Sub-GHz files for PixMob Wave2 wristbands.

The generated one-press files reproduce the exact structure of a signal tested
successfully on a European PixMob Wave2 / Waveband 2 wristband:

* 868.415 MHz OOK
* 500 microsecond bit cells
* group 0 (the universal group)
* 16.6-second wake sequence followed by a persistent RGB command

No third-party Python packages are required.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


FREQUENCY_HZ = 868_415_000
BIT_TIME_US = 500
INTERFRAME_GAP_BITS = 9
WAKE_REPETITIONS = 336
ACTION_REPETITIONS = 20
VALUES_PER_RAW_LINE = 512
GROUP_ALL = 0

# PixMob RF 6-bit -> 8-bit line-code table, in the on-air byte orientation.
LINE_CODE = (
    0x84, 0xAC, 0x34, 0x2C, 0x66, 0x64, 0x35, 0x24,
    0x62, 0x6A, 0x22, 0x2A, 0x26, 0xB6, 0x32, 0x36,
    0x49, 0x4D, 0x65, 0x45, 0x2D, 0x29, 0x61, 0x69,
    0x42, 0x46, 0x54, 0x56, 0x6D, 0x6C, 0x44, 0x4C,
    0x8C, 0x8D, 0xA9, 0xAD, 0x89, 0x99, 0xA1, 0x91,
    0xA5, 0x25, 0x31, 0x21, 0x85, 0x95, 0xB1, 0xB5,
    0x59, 0x51, 0x5A, 0x52, 0x92, 0x9A, 0x4A, 0x8A,
    0xA4, 0xB4, 0x96, 0x94, 0xB2, 0xA2, 0x86, 0xA6,
)
DECODE_LINE_CODE = {encoded: decoded for decoded, encoded in enumerate(LINE_CODE)}

# Two 0xAA preamble bytes followed by the 01 resynchronization bits.
PREAMBLE_AND_SYNC = tuple(int(bit) for bit in "101010101010101001")


@dataclass(frozen=True)
class ColorPreset:
    name: str
    red: int
    green: int
    blue: int


COLORS = (
    ColorPreset("OFF", 0, 0, 0),
    ColorPreset("RED", 252, 0, 0),
    ColorPreset("GREEN", 0, 252, 0),
    ColorPreset("BLUE", 0, 0, 252),
    ColorPreset("WHITE", 252, 252, 252),
    ColorPreset("SOFT_WHITE", 128, 128, 128),
    ColorPreset("WARM_WHITE", 252, 160, 80),
    ColorPreset("COOL_WHITE", 160, 200, 252),
    ColorPreset("YELLOW", 252, 252, 0),
    ColorPreset("CYAN", 0, 252, 252),
    ColorPreset("MAGENTA", 252, 0, 252),
    ColorPreset("ORANGE", 252, 80, 0),
    ColorPreset("GOLD", 252, 160, 0),
    ColorPreset("PURPLE", 128, 0, 252),
    ColorPreset("VIOLET", 200, 0, 252),
    ColorPreset("PINK", 252, 40, 128),
    ColorPreset("LIME", 128, 252, 0),
    ColorPreset("TEAL", 0, 160, 128),
    ColorPreset("AQUA", 0, 252, 160),
    ColorPreset("SKY_BLUE", 0, 128, 252),
)

# Known working wake payload. Decoded fields:
# mode, green, red, blue, attack/random, release/hold, group.
WAKE_BODY = (0, 0, 0, 0, 8, 15, GROUP_ALL)


def calculate_crc12(encoded_body: Sequence[int]) -> int:
    """Calculate the PixMob reversed CRC-12 over seven line-coded bytes."""
    if len(encoded_body) != 7:
        raise ValueError("CRC input must contain exactly seven bytes")

    register = 0xC69
    for byte in encoded_body:
        for bit_index in range(7, -1, -1):
            register ^= (byte >> bit_index) & 1
            register = (register >> 1) ^ 0x8F3 if register & 1 else register >> 1
            register &= 0xFFF
    return register


def encode_body(body: Sequence[int]) -> tuple[int, ...]:
    """Encode seven 6-bit fields into a checked nine-byte RF payload."""
    if len(body) != 7 or any(not 0 <= value <= 0x3F for value in body):
        raise ValueError(f"invalid PixMob body: {body!r}")

    encoded_body = tuple(LINE_CODE[value] for value in body)
    checksum = calculate_crc12(encoded_body)
    frame = (
        LINE_CODE[checksum & 0x3F],
        *encoded_body,
        LINE_CODE[(checksum >> 6) & 0x3F],
    )
    if decode_frame(frame) != tuple(body):
        raise AssertionError("frame failed encode/decode validation")
    return frame


def decode_frame(frame: Sequence[int]) -> tuple[int, ...]:
    """Decode and verify a nine-byte RF payload."""
    if len(frame) != 9 or any(byte not in DECODE_LINE_CODE for byte in frame):
        raise ValueError("frame contains an invalid line-code symbol")

    decoded = tuple(DECODE_LINE_CODE[byte] for byte in frame)
    checksum = calculate_crc12(frame[1:8])
    if decoded[0] != (checksum & 0x3F) or decoded[8] != (checksum >> 6):
        raise ValueError("frame CRC does not match")
    return decoded[1:8]


def persistent_color_body(color: ColorPreset) -> tuple[int, ...]:
    """Create a persistent RGB command addressed to universal group 0."""
    channels = (color.red, color.green, color.blue)
    if any(value % 4 or not 0 <= value <= 252 for value in channels):
        raise ValueError(f"{color.name}: RGB channels must be multiples of four, 0..252")

    mode_persistent = 0x11
    attack_random = 0
    release_hold = 7
    return (
        mode_persistent,
        color.green >> 2,
        color.red >> 2,
        color.blue >> 2,
        attack_random,
        release_hold,
        GROUP_ALL,
    )


def frame_bits(body: Sequence[int]) -> tuple[int, ...]:
    payload = encode_body(body)
    payload_bits = tuple(
        (byte >> bit_index) & 1
        for byte in payload
        for bit_index in range(7, -1, -1)
    )
    return PREAMBLE_AND_SYNC + payload_bits


def build_bitstream(parts: Sequence[tuple[Sequence[int], int]]) -> tuple[int, ...]:
    """Join repeated frames with the observed nine-bit low gap."""
    output: list[int] = []
    for body, repetitions in parts:
        if repetitions < 1:
            raise ValueError("repetition count must be positive")
        encoded = frame_bits(body)
        for _ in range(repetitions):
            if output:
                output.extend([0] * INTERFRAME_GAP_BITS)
            output.extend(encoded)
    return tuple(output)


def bits_to_raw_timings(bits: Sequence[int]) -> tuple[int, ...]:
    """Convert binary OOK levels into signed Flipper RAW microsecond timings."""
    if not bits or bits[0] != 1:
        raise ValueError("bitstream must begin with a high level")

    timings: list[int] = []
    level = bits[0]
    run_length = 0
    for bit in bits:
        if bit == level:
            run_length += 1
            continue
        timings.append(run_length * BIT_TIME_US if level else -run_length * BIT_TIME_US)
        level = bit
        run_length = 1
    timings.append(run_length * BIT_TIME_US if level else -run_length * BIT_TIME_US)
    return tuple(timings)


def raw_timings_to_bits(timings: Sequence[int]) -> tuple[int, ...]:
    """Reconstruct a bitstream from RAW timings for validation."""
    output: list[int] = []
    for index, duration in enumerate(timings):
        if not duration or duration % BIT_TIME_US:
            raise ValueError(f"invalid timing: {duration}")
        if (duration > 0) != (index % 2 == 0):
            raise ValueError("RAW timing signs must alternate")
        output.extend([int(duration > 0)] * (abs(duration) // BIT_TIME_US))
    return tuple(output)


def write_sub_file(
    path: Path,
    parts: Sequence[tuple[Sequence[int], int]],
) -> None:
    """Write and validate a Flipper Sub-GHz RAW file."""
    bitstream = build_bitstream(parts)
    timings = bits_to_raw_timings(bitstream)
    if raw_timings_to_bits(timings) != bitstream:
        raise AssertionError(f"{path.name}: RAW roundtrip failed")

    lines = [
        "Filetype: Flipper SubGhz RAW File",
        "Version: 1",
        f"Frequency: {FREQUENCY_HZ}",
        "Preset: FuriHalSubGhzPresetOok650Async",
        "Protocol: RAW",
    ]
    for start in range(0, len(timings), VALUES_PER_RAW_LINE):
        chunk = timings[start : start + VALUES_PER_RAW_LINE]
        lines.append("RAW_Data: " + " ".join(str(value) for value in chunk))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def validate_known_vectors() -> None:
    """Guard against the endian and CRC mistakes found in older implementations."""
    vectors = {
        WAKE_BODY: (0x56, 0x84, 0x84, 0x84, 0x84, 0x62, 0x36, 0x84, 0x29),
        persistent_color_body(ColorPreset("OFF", 0, 0, 0)):
            (0x66, 0x4D, 0x84, 0x84, 0x84, 0x84, 0x24, 0x84, 0x85),
        persistent_color_body(ColorPreset("RED", 252, 0, 0)):
            (0x51, 0x4D, 0x84, 0xA6, 0x84, 0x84, 0x24, 0x84, 0x4C),
    }
    for body, expected_frame in vectors.items():
        if encode_body(body) != expected_frame:
            raise AssertionError(f"known-vector mismatch for {body!r}")


def generate(output_directory: Path) -> int:
    """Generate all install-ready one-press and quick signal files."""
    validate_known_vectors()
    one_press = output_directory / "one_press"
    quick = output_directory / "quick_after_wake"
    one_press.mkdir(parents=True, exist_ok=True)
    quick.mkdir(parents=True, exist_ok=True)

    for directory in (one_press, quick):
        for stale_file in directory.glob("*.sub"):
            stale_file.unlink()

    write_sub_file(one_press / "00_WAKE_G0.sub", [(WAKE_BODY, WAKE_REPETITIONS)])
    file_count = 1

    for index, color in enumerate(COLORS, start=1):
        body = persistent_color_body(color)
        write_sub_file(
            one_press / f"{index:02d}_{color.name}_G0.sub",
            [(WAKE_BODY, WAKE_REPETITIONS), (body, ACTION_REPETITIONS)],
        )
        write_sub_file(
            quick / f"{index:02d}_{color.name}_G0_QUICK.sub",
            [(body, ACTION_REPETITIONS)],
        )
        file_count += 2

    return file_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "subghz",
        help="directory that receives one_press/ and quick_after_wake/",
    )
    args = parser.parse_args()
    count = generate(args.output.resolve())
    print(f"Generated and validated {count} Flipper .sub files in {args.output.resolve()}")


if __name__ == "__main__":
    main()

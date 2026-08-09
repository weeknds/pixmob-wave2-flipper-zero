#!/usr/bin/env python3
"""Tests for the dependency-free PixMob Wave2 signal generator."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from generator.generate import (
    ACTION_REPETITIONS,
    COLORS,
    FREQUENCY_HZ,
    WAKE_BODY,
    WAKE_REPETITIONS,
    ColorPreset,
    build_bitstream,
    decode_frame,
    encode_body,
    generate,
    persistent_color_body,
)


class CodecTests(unittest.TestCase):
    def test_known_wake_frame(self) -> None:
        self.assertEqual(
            encode_body(WAKE_BODY),
            (0x56, 0x84, 0x84, 0x84, 0x84, 0x62, 0x36, 0x84, 0x29),
        )

    def test_confirmed_red_frame(self) -> None:
        body = persistent_color_body(ColorPreset("RED", 252, 0, 0))
        frame = (0x51, 0x4D, 0x84, 0xA6, 0x84, 0x84, 0x24, 0x84, 0x4C)
        self.assertEqual(encode_body(body), frame)
        self.assertEqual(decode_frame(frame), body)

    def test_off_is_persistent_black_on_group_zero(self) -> None:
        self.assertEqual(
            persistent_color_body(ColorPreset("OFF", 0, 0, 0)),
            (0x11, 0, 0, 0, 0, 7, 0),
        )

    def test_one_press_duration_is_about_seventeen_seconds(self) -> None:
        red = persistent_color_body(ColorPreset("RED", 252, 0, 0))
        bit_count = len(
            build_bitstream([(WAKE_BODY, WAKE_REPETITIONS), (red, ACTION_REPETITIONS)])
        )
        self.assertGreater(bit_count * 500 / 1_000_000, 17.0)
        self.assertLess(bit_count * 500 / 1_000_000, 18.0)


class OutputTests(unittest.TestCase):
    def test_every_file_has_valid_flipper_header(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            count = generate(output)
            files = sorted(output.rglob("*.sub"))
            self.assertEqual(count, 1 + 2 * len(COLORS))
            self.assertEqual(len(files), count)

            expected = [
                "Filetype: Flipper SubGhz RAW File",
                "Version: 1",
                f"Frequency: {FREQUENCY_HZ}",
                "Preset: FuriHalSubGhzPresetOok650Async",
                "Protocol: RAW",
            ]
            for path in files:
                lines = path.read_text(encoding="ascii").splitlines()
                self.assertEqual(lines[:5], expected)
                self.assertTrue(all(line.startswith("RAW_Data: ") for line in lines[5:]))
                self.assertTrue(
                    all(len(line.split()) - 1 <= 512 for line in lines[5:]),
                    path.name,
                )


if __name__ == "__main__":
    unittest.main()

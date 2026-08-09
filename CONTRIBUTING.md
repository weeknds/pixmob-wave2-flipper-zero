# Contributing

Reports from other PixMob hardware revisions and regions are welcome.

When opening an issue, include as much of the following as possible:

- The exact model and PCB markings.
- The event country or likely RF region.
- Whether `02_RED_G0.sub` works.
- Battery type and whether the batteries are fresh.
- Flipper firmware version and configured region.
- A clean Sub-GHz RAW recording, when available.

Before submitting code, regenerate the signal files and run the tests:

```bash
python3 generator/generate.py
python3 -m unittest discover -s tests -v
git diff --exit-code
```

Please do not add unverified frequencies or instructions for bypassing regional
transmission restrictions.

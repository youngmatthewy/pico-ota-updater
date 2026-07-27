# Pico OTA Updater

Reusable over-the-air application updater for Raspberry Pi Pico W and Pico 2 W devices running MicroPython.

## Repository structure

```text
pico-ota-updater/
├── src/
│   └── pico_ota/             Reusable MicroPython package
├── tests/                    Desktop-side pytest suite
├── tools/
│   ├── build_manifest.py     Generates application release manifests
│   └── vendor_to_app.py      Copies the package into an application
├── examples/
│   └── basic/                Minimal Pico boot and application example
├── .github/workflows/test.yml
├── pyproject.toml
├── README.md
└── LICENSE
```

The repository uses a standard Python `src` layout for desktop testing and packaging.
A Pico application still receives the package under `lib/pico_ota/`, because MicroPython searches `lib` on the device.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pytest
pytest
```

Expected result:

```text
6 passed
```

## Copying the updater into a Pico application

```bash
python tools/vendor_to_app.py ~/projects/pico-ota-test-app
```

This produces:

```text
pico-ota-test-app/
└── lib/
    └── pico_ota/
```

## Features

- Remote JSON manifest checks
- Semantic version comparison
- HTTPS file downloads
- SHA-256 verification
- `.new` staging files
- `.bak` rollback files
- Trial-boot confirmation
- Automatic rollback after a failed trial boot
- Protected device-local and updater files
- Stable or beta update channels
- Confirmed version state stored in `.ota_state.json`

## Protected files

The initial implementation does not update:

- `boot.py`
- `lib/pico_ota/`
- `secrets.py`
- `device_config.py`
- `device_config.json`

## Application update sequence

1. `boot.py` checks for unfinished updates.
2. The updater downloads a newer application release into `.new` files.
3. SHA-256 hashes and file sizes are verified.
4. Current application files become `.bak` files.
5. New files are activated.
6. The Pico resets.
7. The first reboot is marked as a trial boot.
8. The application initializes.
9. The application calls `mark_boot_successful()`.
10. Backups are removed and the confirmed version is saved.

A second reboot before confirmation triggers rollback.

## Scope

This project updates MicroPython application files. It does not update the MicroPython UF2 firmware.

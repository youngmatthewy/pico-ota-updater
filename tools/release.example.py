#!/usr/bin/env python3
"""
Generic OTA manifest release wrapper.

Copy this file into an application repository as:

    tools/release.py

Then edit the CONFIGURATION section below.

Usage:

    python tools/release.py 0.1.0

or, after making it executable:

    ./tools/release.py 0.1.0
"""

import argparse
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Application name expected by OTAConfig on the Pico.
APPLICATION = "your-application-name"

# GitHub raw-content base URL for the application's deploy branch.
BASE_URL = (
    "https://raw.githubusercontent.com/"
    "YOUR_GITHUB_USERNAME/YOUR_REPOSITORY/deploy"
)

# OTA release channel.
CHANNEL = "stable"

# Files and directories managed through OTA.
#
# Do not include protected or device-specific files such as:
#   boot.py
#   lib/pico_ota/
#   secrets.py
#   device_config.py
INCLUDE_PATHS = [
    "main.py",
    "app",
]

# Location of the generated manifest, relative to the application root.
OUTPUT_PATH = "release/manifest.json"


# ---------------------------------------------------------------------------
# IMPLEMENTATION
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_BUILDER = PROJECT_ROOT / "tools" / "build_manifest.py"
OUTPUT = PROJECT_ROOT / OUTPUT_PATH


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build an OTA manifest for this application."
    )
    parser.add_argument(
        "version",
        help="Release version, for example 0.1.0",
    )
    return parser.parse_args()


def validate_configuration():
    errors = []

    if APPLICATION == "your-application-name":
        errors.append("Set APPLICATION in tools/release.py")

    if "YOUR_GITHUB_USERNAME" in BASE_URL:
        errors.append("Set the GitHub username in BASE_URL")

    if "YOUR_REPOSITORY" in BASE_URL:
        errors.append("Set the repository name in BASE_URL")

    if not MANIFEST_BUILDER.exists():
        errors.append(
            "Manifest builder not found at %s" % MANIFEST_BUILDER
        )

    for include_path in INCLUDE_PATHS:
        path = PROJECT_ROOT / include_path
        if not path.exists():
            errors.append(
                "Included path does not exist: %s" % include_path
            )

    if errors:
        for error in errors:
            print("Error:", error, file=sys.stderr)
        raise SystemExit(1)


def build_command(version):
    command = [
        sys.executable,
        str(MANIFEST_BUILDER),
        "--root",
        str(PROJECT_ROOT),
        "--base-url",
        BASE_URL,
        "--application",
        APPLICATION,
        "--version",
        version,
        "--channel",
        CHANNEL,
        "--include",
    ]

    command.extend(INCLUDE_PATHS)

    command.extend(
        [
            "--output",
            str(OUTPUT),
        ]
    )

    return command


def main():
    args = parse_args()
    validate_configuration()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        build_command(args.version),
        cwd=PROJECT_ROOT,
        check=True,
    )

    print()
    print("OTA manifest created successfully")
    print("Application:", APPLICATION)
    print("Version:", args.version)
    print("Channel:", CHANNEL)
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()

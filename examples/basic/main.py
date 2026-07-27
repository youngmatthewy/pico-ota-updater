import time

from device_config import (
    APP_NAME,
    APP_VERSION,
    MANIFEST_URL,
    UPDATE_CHANNEL,
)
from pico_ota import OTAConfig, OTAUpdater


def initialize_application():
    # Initialize sensors, web server, state, and other required services here.
    print("Application initialized")


def run_application():
    while True:
        # Replace this loop with the actual application.
        print("Application heartbeat")
        time.sleep(10)


config = OTAConfig(
    manifest_url=MANIFEST_URL,
    application=APP_NAME,
    current_version=APP_VERSION,
    channel=UPDATE_CHANNEL,
)
updater = OTAUpdater(config)

try:
    initialize_application()

    # Call only after the application has reached a known-good state.
    updater.mark_boot_successful()

    run_application()
except Exception as exc:
    print("Application crashed:", exc)

    # Leave the pending marker intact. The next reboot will restore backups.
    time.sleep(3)
    updater.reset()

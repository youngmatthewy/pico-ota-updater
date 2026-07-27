import gc
import time
import network

from secrets import WIFI_PASSWORD, WIFI_SSID
from device_config import (
    APP_NAME,
    APP_VERSION,
    MANIFEST_URL,
    UPDATE_CHANNEL,
)
from pico_ota import OTAConfig, OTAUpdater


def connect_wifi(timeout_seconds=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    deadline = time.ticks_add(time.ticks_ms(), timeout_seconds * 1000)

    while not wlan.isconnected():
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            raise RuntimeError("Wi-Fi connection timed out")
        time.sleep_ms(250)

    return wlan


config = OTAConfig(
    manifest_url=MANIFEST_URL,
    application=APP_NAME,
    current_version=APP_VERSION,
    channel=UPDATE_CHANNEL,
)

updater = OTAUpdater(config)

# If the prior update never reported a successful application boot,
# restore the previous application before doing anything else.
boot_state = updater.recover_if_needed()

if boot_state == "normal":
    try:
        connect_wifi()

        if updater.check_and_install():
            time.sleep_ms(500)
            updater.reset()

    except Exception as exc:
        print("OTA check skipped:", exc)

elif boot_state == "trial":
    # Do not check GitHub during a trial boot.
    # main.py must run and confirm the update.
    print("OTA: update check deferred during trial boot")

elif boot_state == "rolled_back":
    # Do not immediately perform another update after rollback.
    # Run the restored application first.
    print("OTA: update check deferred after rollback")

gc.collect()

import json
from pathlib import Path

from pico_ota import OTAConfig, OTAUpdater


def make_updater():
    config = OTAConfig(
        manifest_url="https://example.com/manifest.json",
        application="test-app",
        current_version="0.1.0",
        channel="stable",
    )
    return OTAUpdater(config, logger=None)


def test_first_pending_boot_is_allowed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()
    Path(".ota_pending.json").write_text(
        json.dumps({
            "application": "test-app",
            "version": "0.2.0",
            "channel": "stable",
            "phase": "installed",
            "files": [{"path": "main.py"}],
        }),
        encoding="utf-8",
    )

    assert updater.recover_if_needed() is False
    pending = json.loads(Path(".ota_pending.json").read_text(encoding="utf-8"))
    assert pending["phase"] == "booting"


def test_second_unconfirmed_boot_rolls_back(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()
    Path("main.py").write_text("broken", encoding="utf-8")
    Path("main.py.bak").write_text("working", encoding="utf-8")
    Path(".ota_pending.json").write_text(
        json.dumps({
            "application": "test-app",
            "version": "0.2.0",
            "channel": "stable",
            "phase": "booting",
            "files": [{"path": "main.py"}],
        }),
        encoding="utf-8",
    )

    assert updater.recover_if_needed() is True
    assert Path("main.py").read_text(encoding="utf-8") == "working"
    assert not Path(".ota_pending.json").exists()


def test_confirmed_state_controls_installed_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()
    Path(".ota_state.json").write_text(
        json.dumps({
            "application": "test-app",
            "version": "0.2.0",
            "channel": "stable",
        }),
        encoding="utf-8",
    )

    assert updater.installed_version() == "0.2.0"
    assert updater.update_available({"version": "0.2.0"}) is False
    assert updater.update_available({"version": "0.3.0"}) is True

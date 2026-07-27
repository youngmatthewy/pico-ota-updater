import json
from pathlib import Path

from pico_ota import OTAConfig, OTAUpdater


def make_updater():
    config = OTAConfig(
        manifest_url="https://example.com/manifest.json",
        application="test-app",
        current_version="0.2.0",
        channel="stable",
    )
    return OTAUpdater(config, logger=None)


def test_failed_version_is_skipped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path(".ota_failed.json").write_text(
        json.dumps(
            {
                "application": "test-app",
                "channel": "stable",
                "version": "0.3.0",
            }
        ),
        encoding="utf-8",
    )

    assert updater.failed_version() == "0.3.0"
    assert updater.update_available({"version": "0.3.0"}) is False
    assert updater.update_available({"version": "0.3.1"}) is True


def test_rollback_records_failed_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path("main.py").write_text("broken", encoding="utf-8")
    Path("main.py.bak").write_text("working", encoding="utf-8")

    Path(".ota_pending.json").write_text(
        json.dumps(
            {
                "application": "test-app",
                "version": "0.3.0",
                "channel": "stable",
                "phase": "booting",
                "files": [{"path": "main.py"}],
            }
        ),
        encoding="utf-8",
    )

    assert updater.recover_if_needed() is True
    assert Path("main.py").read_text(encoding="utf-8") == "working"

    failed = json.loads(
        Path(".ota_failed.json").read_text(encoding="utf-8")
    )
    assert failed["version"] == "0.3.0"


def test_successful_newer_version_clears_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path(".ota_failed.json").write_text(
        json.dumps(
            {
                "application": "test-app",
                "channel": "stable",
                "version": "0.3.0",
            }
        ),
        encoding="utf-8",
    )

    Path(".ota_pending.json").write_text(
        json.dumps(
            {
                "application": "test-app",
                "version": "0.3.1",
                "channel": "stable",
                "phase": "booting",
                "files": [{"path": "main.py"}],
            }
        ),
        encoding="utf-8",
    )

    Path("main.py").write_text("working", encoding="utf-8")
    Path("main.py.bak").write_text("old", encoding="utf-8")

    assert updater.mark_boot_successful() is True
    assert not Path(".ota_failed.json").exists()

    state = json.loads(
        Path(".ota_state.json").read_text(encoding="utf-8")
    )
    assert state["version"] == "0.3.1"

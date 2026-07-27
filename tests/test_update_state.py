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


def write_pending_update(version, phase):
    Path(".ota_pending.json").write_text(
        json.dumps(
            {
                "application": "test-app",
                "version": version,
                "channel": "stable",
                "phase": phase,
                "files": [{"path": "main.py"}],
            }
        ),
        encoding="utf-8",
    )


def test_no_pending_update_returns_normal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    assert updater.recover_if_needed() == "normal"


def test_first_pending_boot_returns_trial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    write_pending_update(
        version="0.2.0",
        phase="installed",
    )

    assert updater.recover_if_needed() == "trial"

    pending = json.loads(
        Path(".ota_pending.json").read_text(encoding="utf-8")
    )
    assert pending["phase"] == "booting"


def test_trial_boot_preserves_working_backup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path("main.py").write_text(
        "broken",
        encoding="utf-8",
    )
    Path("main.py.bak").write_text(
        "working",
        encoding="utf-8",
    )

    write_pending_update(
        version="0.2.0",
        phase="installed",
    )

    assert updater.recover_if_needed() == "trial"
    assert Path("main.py").read_text(
        encoding="utf-8"
    ) == "broken"
    assert Path("main.py.bak").read_text(
        encoding="utf-8"
    ) == "working"


def test_second_unconfirmed_boot_rolls_back(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path("main.py").write_text(
        "broken",
        encoding="utf-8",
    )
    Path("main.py.bak").write_text(
        "working",
        encoding="utf-8",
    )

    write_pending_update(
        version="0.2.0",
        phase="booting",
    )

    assert updater.recover_if_needed() == "rolled_back"
    assert Path("main.py").read_text(
        encoding="utf-8"
    ) == "working"
    assert not Path("main.py.bak").exists()
    assert not Path(".ota_pending.json").exists()


def test_rollback_records_failed_version(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path("main.py").write_text(
        "broken",
        encoding="utf-8",
    )
    Path("main.py.bak").write_text(
        "working",
        encoding="utf-8",
    )

    write_pending_update(
        version="0.2.0",
        phase="booting",
    )

    assert updater.recover_if_needed() == "rolled_back"

    failed = json.loads(
        Path(".ota_failed.json").read_text(encoding="utf-8")
    )

    assert failed == {
        "application": "test-app",
        "channel": "stable",
        "version": "0.2.0",
    }


def test_failed_version_is_skipped(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path(".ota_failed.json").write_text(
        json.dumps(
            {
                "application": "test-app",
                "channel": "stable",
                "version": "0.2.0",
            }
        ),
        encoding="utf-8",
    )

    assert updater.failed_version() == "0.2.0"
    assert updater.update_available({"version": "0.2.0"}) is False
    assert updater.update_available({"version": "0.2.1"}) is True


def test_confirmed_state_controls_installed_version(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    updater = make_updater()

    Path(".ota_state.json").write_text(
        json.dumps(
            {
                "application": "test-app",
                "version": "0.2.0",
                "channel": "stable",
            }
        ),
        encoding="utf-8",
    )

    assert updater.installed_version() == "0.2.0"
    assert updater.update_available({"version": "0.2.0"}) is False
    assert updater.update_available({"version": "0.3.0"}) is True

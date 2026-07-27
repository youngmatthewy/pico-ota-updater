try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

try:
    import ubinascii as binascii
except ImportError:
    import binascii

try:
    import machine
except ImportError:
    machine = None

from .errors import IntegrityError, ManifestError, StorageError
from .http import download_to_file, get_json
from .manifest import normalize_path, validate_manifest
from .storage import (
    ensure_parent,
    exists,
    read_json,
    remove_if_exists,
    rename,
    write_json_atomic,
)
from .version import is_newer


class OTAUpdater:
    def __init__(self, config, logger=print):
        self.config = config
        self.log = logger or (lambda *_: None)

    def fetch_manifest(self):
        self.log("OTA: checking manifest")
        manifest = get_json(
            self.config.manifest_url,
            timeout_seconds=self.config.timeout_seconds,
        )
        validate_manifest(manifest)

        if manifest["application"] != self.config.application:
            raise ManifestError(
                "Manifest application %s does not match %s"
                % (manifest["application"], self.config.application)
            )

        if manifest["channel"] != self.config.channel:
            raise ManifestError(
                "Manifest channel %s does not match %s"
                % (manifest["channel"], self.config.channel)
            )

        return manifest

    def installed_version(self):
        state = read_json(self.config.state_file, default=None)
        if (
            state
            and state.get("application") == self.config.application
            and state.get("channel") == self.config.channel
            and state.get("version")
        ):
            return state["version"]
        return self.config.current_version

    def failed_version(self):
        failed = read_json(self.config.failed_file, default=None)

        if not failed:
            return None

        if failed.get("application") != self.config.application:
            return None

        if failed.get("channel") != self.config.channel:
            return None

        return failed.get("version")


    def mark_version_failed(self, version):
        state = {
            "application": self.config.application,
            "channel": self.config.channel,
            "version": version,
        }
        write_json_atomic(self.config.failed_file, state)
        self.log("OTA: recorded failed version %s" % version)


    def clear_failed_version(self, version=None):
        failed = read_json(self.config.failed_file, default=None)

        if not failed:
            return False

        if failed.get("application") != self.config.application:
            return False

        if failed.get("channel") != self.config.channel:
            return False

        if version is not None and failed.get("version") != version:
            return False

        remove_if_exists(self.config.failed_file)
        self.log("OTA: cleared failed-version record")
        return True 

    def update_available(self, manifest):
        candidate = manifest["version"]

        if candidate == self.failed_version():
            self.log(
                "OTA: skipping previously failed version %s"
                % candidate
            )
            return False

        return is_newer(candidate, self.installed_version())
       
    def check_and_install(self):
        manifest = self.fetch_manifest()

        if not self.update_available(manifest):
            self.log(
                "OTA: current version %s is up to date"
                % self.installed_version()
            )
            return False

        self.log(
            "OTA: update available %s -> %s"
            % (self.installed_version(), manifest["version"])
        )
        self.install(manifest)
        return True

    def install(self, manifest):
        files = self._validated_update_files(manifest)
        self._clear_staging(files)
        self._download_all(files)
        self._write_pending_marker(manifest, files)

        try:
            self._activate(files)
        except Exception:
            self.log("OTA: activation failed, restoring backups")
            self._rollback_files(files)
            raise

        self.log("OTA: update installed; reboot required")

    def recover_if_needed(self):
        pending = read_json(self.config.pending_marker, default=None)
        if not pending:
            return False

        phase = pending.get("phase", "installed")

        # The first reboot after activation is the new application's trial boot.
        # Mark it before main.py starts. If the device resets again without
        # mark_boot_successful(), the next boot restores the backups.
        if phase == "installed":
            pending["phase"] = "booting"
            write_json_atomic(self.config.pending_marker, pending)
            self.log("OTA: starting trial boot for version %s" % pending.get("version"))
            return False

        files = pending.get("files", [])
        failed_version = pending.get("version")

        self.log("OTA: trial boot failed; rolling back")
        self._rollback_files(files)

        if failed_version:
            self.mark_version_failed(failed_version)

        remove_if_exists(self.config.pending_marker)
        return True

    def mark_boot_successful(self):
        pending = read_json(self.config.pending_marker, default=None)
        if not pending:
            return False

        for item in pending.get("files", []):
            path = normalize_path(item["path"])
            remove_if_exists(path + ".bak")
            remove_if_exists(path + ".new")

        state = {
            "application": pending.get("application"),
            "version": pending.get("version"),
            "channel": pending.get("channel"),
        }
        write_json_atomic(self.config.state_file, state)

        failed = self.failed_version()
        if failed and failed != state["version"]:
            self.clear_failed_version()

        remove_if_exists(self.config.pending_marker)
        self.log("OTA: boot confirmed; backups removed")
        return True

    def reset(self):
        if machine is None:
            raise RuntimeError("machine.reset is only available on MicroPython")
        machine.reset()

    def _validated_update_files(self, manifest):
        output = []
        for raw_item in manifest["files"]:
            item = dict(raw_item)
            item["path"] = normalize_path(item["path"])
            self._assert_not_protected(item["path"])
            output.append(item)
        return output

    def _assert_not_protected(self, path):
        for protected in self.config.protected_paths:
            normalized = normalize_path(protected)
            if path == normalized or path.startswith(normalized.rstrip("/") + "/"):
                raise ManifestError("Manifest attempts to replace protected path: %s" % path)

    def _clear_staging(self, files):
        for item in files:
            path = item["path"]
            remove_if_exists(path + ".new")

    def _download_all(self, files):
        for item in files:
            path = item["path"]
            destination = path + ".new"
            ensure_parent(destination)

            self.log("OTA: downloading %s" % path)
            hasher = hashlib.sha256()
            actual_size = download_to_file(
                item["url"],
                destination,
                hasher,
                chunk_size=self.config.chunk_size,
                timeout_seconds=self.config.timeout_seconds,
            )

            expected_size = int(item["size"])
            if actual_size != expected_size:
                remove_if_exists(destination)
                raise IntegrityError(
                    "Size mismatch for %s: expected %s, got %s"
                    % (path, expected_size, actual_size)
                )

            actual_hash = binascii.hexlify(hasher.digest()).decode().lower()
            expected_hash = item["sha256"].lower()

            if actual_hash != expected_hash:
                remove_if_exists(destination)
                raise IntegrityError(
                    "SHA-256 mismatch for %s" % path
                )

    def _write_pending_marker(self, manifest, files):
        marker = {
            "application": manifest["application"],
            "version": manifest["version"],
            "channel": manifest["channel"],
            "phase": "installed",
            "files": [{"path": item["path"]} for item in files],
        }
        write_json_atomic(self.config.pending_marker, marker)

    def _activate(self, files):
        activated = []

        try:
            for item in files:
                path = item["path"]
                new_path = path + ".new"
                backup_path = path + ".bak"

                remove_if_exists(backup_path)
                if exists(path):
                    rename(path, backup_path)

                rename(new_path, path)
                activated.append(path)
        except Exception:
            self._rollback_files([{"path": path} for path in activated] + files)
            raise

    def _rollback_files(self, files):
        seen = set()

        for item in files:
            path = normalize_path(item["path"])
            if path in seen:
                continue
            seen.add(path)

            backup_path = path + ".bak"
            new_path = path + ".new"

            if exists(backup_path):
                remove_if_exists(path)
                rename(backup_path, path)

            remove_if_exists(new_path)

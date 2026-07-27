try:
    import ujson as json
except ImportError:
    import json

import os

from .errors import StorageError


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def ensure_parent(path):
    parts = path.split("/")[:-1]
    current = ""

    for part in parts:
        current = part if not current else current + "/" + part
        if not exists(current):
            try:
                os.mkdir(current)
            except OSError as exc:
                raise StorageError("Could not create %s: %s" % (current, exc))


def remove_if_exists(path):
    if exists(path):
        try:
            os.remove(path)
        except OSError as exc:
            raise StorageError("Could not remove %s: %s" % (path, exc))


def rename(source, destination):
    try:
        os.rename(source, destination)
    except OSError as exc:
        raise StorageError(
            "Could not rename %s to %s: %s" % (source, destination, exc)
        )


def write_json_atomic(path, value):
    temporary = path + ".tmp"
    ensure_parent(path)

    try:
        with open(temporary, "w") as target:
            json.dump(value, target)
        remove_if_exists(path)
        rename(temporary, path)
    except Exception as exc:
        try:
            remove_if_exists(temporary)
        except Exception:
            pass
        raise StorageError("Could not write %s: %s" % (path, exc))


def read_json(path, default=None):
    if not exists(path):
        return default

    try:
        with open(path, "r") as source:
            return json.load(source)
    except Exception as exc:
        raise StorageError("Could not read %s: %s" % (path, exc))

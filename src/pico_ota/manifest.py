from .errors import ManifestError


REQUIRED_TOP_LEVEL = (
    "schema_version",
    "application",
    "version",
    "channel",
    "files",
)

REQUIRED_FILE_FIELDS = (
    "path",
    "url",
    "sha256",
    "size",
)


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise ManifestError("Manifest must be a JSON object")

    for field in REQUIRED_TOP_LEVEL:
        if field not in manifest:
            raise ManifestError("Manifest is missing %s" % field)

    if manifest["schema_version"] != 1:
        raise ManifestError(
            "Unsupported manifest schema: %s" % manifest["schema_version"]
        )

    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise ManifestError("Manifest files must be a non-empty list")

    seen = set()
    for item in files:
        if not isinstance(item, dict):
            raise ManifestError("Each manifest file entry must be an object")

        for field in REQUIRED_FILE_FIELDS:
            if field not in item:
                raise ManifestError("File entry is missing %s" % field)

        path = normalize_path(item["path"])
        if path in seen:
            raise ManifestError("Duplicate manifest path: %s" % path)
        seen.add(path)

        if not item["url"].startswith(("http://", "https://")):
            raise ManifestError("Invalid URL for %s" % path)

        digest = item["sha256"].lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ManifestError("Invalid SHA-256 for %s" % path)

        if int(item["size"]) < 0:
            raise ManifestError("Invalid size for %s" % path)

    return manifest


def normalize_path(path):
    if not isinstance(path, str) or not path:
        raise ManifestError("File path must be a non-empty string")

    value = path.replace("\\", "/").lstrip("/")
    pieces = [piece for piece in value.split("/") if piece not in ("", ".")]

    if not pieces or any(piece == ".." for piece in pieces):
        raise ManifestError("Unsafe file path: %s" % path)

    return "/".join(pieces)

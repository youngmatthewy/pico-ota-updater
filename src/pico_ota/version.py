def _normalize(version):
    if not isinstance(version, str):
        raise ValueError("Version must be a string")

    value = version.strip()
    if value.startswith("v"):
        value = value[1:]

    core = value.split("+", 1)[0]
    core = core.split("-", 1)[0]
    parts = core.split(".")

    if not parts or any(not part.isdigit() for part in parts):
        raise ValueError("Unsupported version format: %s" % version)

    numbers = [int(part) for part in parts]
    while len(numbers) < 3:
        numbers.append(0)

    return tuple(numbers)


def compare_versions(left, right):
    left_parts = _normalize(left)
    right_parts = _normalize(right)

    if left_parts < right_parts:
        return -1
    if left_parts > right_parts:
        return 1
    return 0


def is_newer(candidate, current):
    return compare_versions(candidate, current) > 0

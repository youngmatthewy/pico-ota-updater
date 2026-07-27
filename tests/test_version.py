from pico_ota.version import compare_versions, is_newer


def test_version_comparison():
    assert compare_versions("1.0.0", "1.0.0") == 0
    assert compare_versions("1.0.1", "1.0.0") == 1
    assert compare_versions("1.0.0", "1.0.1") == -1
    assert compare_versions("v2.1", "2.0.9") == 1


def test_is_newer():
    assert is_newer("0.2.0", "0.1.9")
    assert not is_newer("0.1.0", "0.1.0")

from tools.build_manifest import build_manifest


def test_manifest_builder(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    app = tmp_path / "app"
    app.mkdir()
    (app / "sensor.py").write_text("VALUE = 1\n", encoding="utf-8")

    manifest = build_manifest(
        root=tmp_path,
        base_url="https://example.com/deploy",
        application="test-app",
        version="1.2.3",
        channel="stable",
        include_paths=["main.py", "app"],
    )

    assert manifest["application"] == "test-app"
    assert manifest["version"] == "1.2.3"
    assert len(manifest["files"]) == 2
    assert all(item["sha256"] for item in manifest["files"])

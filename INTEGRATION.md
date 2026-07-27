# Application integration

## Copy the package

```bash
python tools/vendor_to_app.py /path/to/application
```

## Device-local files

Create `secrets.py` and `device_config.py` in the application repository, but exclude them from Git.

## Boot flow

Use `examples/basic/boot.py` as the starting point. It:

1. Builds the updater configuration.
2. handles an incomplete trial boot.
3. Connects to Wi-Fi.
4. Checks for an application release.
5. Installs and resets when a release is available.
6. Continues booting when GitHub or Wi-Fi is unavailable.

## Startup confirmation

Call `mark_boot_successful()` only after essential application initialization has succeeded.

## Manifest generation

```bash
python tools/build_manifest.py \
  --root . \
  --base-url https://raw.githubusercontent.com/USER/APP/deploy \
  --application APP_NAME \
  --version 0.2.0 \
  --channel stable \
  --include main.py app static \
  --output release/manifest.json
```

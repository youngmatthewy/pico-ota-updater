from .errors import ConfigurationError


class OTAConfig:
    DEFAULT_PROTECTED_PATHS = (
        "boot.py",
        "secrets.py",
        "device_config.py",
        "device_config.json",
        "lib/pico_ota",
    )

    def __init__(
        self,
        manifest_url,
        application,
        current_version,
        channel="stable",
        protected_paths=None,
        timeout_seconds=20,
        chunk_size=1024,
        pending_marker=".ota_pending.json",
        state_file=".ota_state.json",
    ):
        self.manifest_url = manifest_url
        self.application = application
        self.current_version = current_version
        self.channel = channel
        self.protected_paths = tuple(
            protected_paths or self.DEFAULT_PROTECTED_PATHS
        )
        self.timeout_seconds = int(timeout_seconds)
        self.chunk_size = int(chunk_size)
        self.pending_marker = pending_marker
        self.state_file = state_file
        self.validate()

    def validate(self):
        if (
            not isinstance(self.manifest_url, str)
            or not (
                self.manifest_url.startswith("http://")
                or self.manifest_url.startswith("https://")
            )
        ):
            raise ConfigurationError("manifest_url must be an HTTP or HTTPS URL")
        if not self.application:
            raise ConfigurationError("application is required")
        if not self.current_version:
            raise ConfigurationError("current_version is required")
        if self.chunk_size < 128:
            raise ConfigurationError("chunk_size must be at least 128 bytes")

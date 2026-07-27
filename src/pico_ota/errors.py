class OTAError(Exception):
    pass


class ConfigurationError(OTAError):
    pass


class NetworkError(OTAError):
    pass


class ManifestError(OTAError):
    pass


class IntegrityError(OTAError):
    pass


class StorageError(OTAError):
    pass

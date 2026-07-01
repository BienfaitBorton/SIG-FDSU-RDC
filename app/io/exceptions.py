class IOError(Exception):
    """Erreur générique pour le module IO."""


class ValidationError(IOError):
    pass


class FormatNotSupported(IOError):
    pass


class DependencyMissing(IOError):
    pass

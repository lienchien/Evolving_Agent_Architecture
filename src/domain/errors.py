class CapabilityConflictError(Exception):
    """A stale write or a capability uniqueness constraint rejected an operation."""


class IllegalTransitionError(CapabilityConflictError):
    pass


class UnknownCapabilityError(ValueError):
    pass


class TelemetryConflictError(Exception):
    """A telemetry uniqueness or correlation constraint rejected a write."""


class UnknownTraceError(ValueError):
    """A requested execution trace does not exist."""


class UnsupportedTelemetrySchemaError(RuntimeError):
    """The database schema is newer than this application understands."""

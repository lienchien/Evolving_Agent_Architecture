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


class ProviderOperationError(RuntimeError):
    """A provider adapter failed during a known, auditable operation.

    The original exception remains available for normalized telemetry without
    persisting its potentially sensitive message.
    """

    def __init__(
        self,
        *,
        operation: str,
        provider_name: str,
        cause: Exception,
    ) -> None:
        super().__init__(str(cause))
        self.operation = operation
        self.provider_name = provider_name
        self.cause = cause

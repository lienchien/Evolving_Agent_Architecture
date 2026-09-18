class CapabilityConflictError(Exception):
    """A stale write or a capability uniqueness constraint rejected an operation."""


class IllegalTransitionError(CapabilityConflictError):
    pass


class UnknownCapabilityError(ValueError):
    pass

from __future__ import annotations


class PolicyService:
    """Placeholder policy gate; every check currently allows the action.

    Kept as a real dependency (not inlined) so a future rules engine can be
    swapped in without touching the services that call it.
    """

    def can_generate(self, *_args, **_kwargs) -> bool:
        return True

    def can_validate(self, *_args, **_kwargs) -> bool:
        return True

    def can_execute(self, *_args, **_kwargs) -> bool:
        return True

    def can_activate(self, *_args, **_kwargs) -> bool:
        return True

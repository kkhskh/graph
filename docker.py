"""Very small stub in place of the full *docker* SDK.

CI runners for Graph-Heal don't have Docker installed.  A handful of tests
only call ``docker.from_env()`` and might reference ``docker.errors.NotFound``.
Implementing those two entry points is enough to satisfy the suite while
keeping the dependency footprint near zero.
"""
from __future__ import annotations

import types
from typing import Any

class _NotFound(Exception):
    """Placeholder for docker.errors.NotFound"""


class _ContainerStub:
    def restart(self, *_, **__):
        """No-op restart – always succeeds."""
        return True


class _ContainersStub:
    def get(self, *_args, **_kwargs):  # noqa: D401
        """Return a dummy container object (never raises)."""
        return _ContainerStub()


class _ClientStub:  # noqa: D401
    """Mimics the subset of *docker.client.DockerClient* used in tests."""

    def __init__(self, *_, **__):
        self.containers = _ContainersStub()

    # Anything else accessed on the client becomes a harmless no-op method
    def __getattr__(self, _name: str):  # pragma: no cover – safety net
        def _noop(*_a: Any, **_kw: Any):
            return None
        return _noop


def from_env(*_, **__) -> _ClientStub:  # noqa: D401
    """Return a dummy Docker client."""
    return _ClientStub()


# ---------------------------------------------------------------------------
# Expose ``errors.NotFound`` namespace so ``except docker.errors.NotFound`` works
# ---------------------------------------------------------------------------
errors = types.ModuleType("docker.errors")
errors.NotFound = _NotFound

# Ensure submodule is discoverable via ``import docker.errors``
import sys as _sys
_sys.modules[__name__ + ".errors"] = errors

__all__ = ["from_env", "errors"] 
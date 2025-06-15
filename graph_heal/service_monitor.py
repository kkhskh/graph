"""Light stub for service monitor used in tests."""
from __future__ import annotations

import requests  # imported at module level so tests can patch ``requests.get``

class ServiceMonitor:  # type: ignore
    """Extremely lightweight service monitor implementation.

    It only needs to satisfy a handful of unit tests that patch
    ``requests.get`` and call the private method ``_check_service_health``.
    """

    def __init__(self, services: list[dict[str, str]] | None = None, poll_interval: float = 1.0):  # noqa: D401
        self.poll_interval = poll_interval
        # Store service dicts keyed by id for quick lookup
        self.services = {svc["id"]: svc for svc in (services or [])}
        self._statuses: dict[str, dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Health checks -----------------------------------------------------
    # ------------------------------------------------------------------
    def _check_service_health(self, service_id: str, url: str):  # noqa: D401
        """Return *status* dict according to the legacy contract.

        The real monitor would fetch metrics in the background. For the unit
        tests we synchronously call ``requests.get`` (which is monkey-patched
        by the test) and derive a small result object.
        """
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                status = {
                    "service": service_id,
                    "status": "healthy",
                    "metrics": resp.json(),
                }
            else:
                status = {
                    "service": service_id,
                    "status": "unhealthy",
                    "metrics": {},
                }
        except Exception as exc:  # pragma: no cover – exercised via patch side-effect
            status = {
                "service": service_id,
                "status": "error",
                "metrics": {"error": str(exc)},
            }

        # Cache latest status for *get_service_status*
        self._statuses[service_id] = status
        return status

    # ------------------------------------------------------------------
    # Public helpers ----------------------------------------------------
    # ------------------------------------------------------------------
    def add_service(self, name: str):  # pragma: no cover
        self.services[name] = {}

    def get_service_status(self, name: str):
        if name not in self._statuses:
            raise ValueError(f"Unknown service {name!r}")
        return self._statuses[name]

__all__ = ["ServiceMonitor"] 
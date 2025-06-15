"""Light stub for service monitor used in tests."""
from __future__ import annotations

class ServiceMonitor:  # type: ignore
    def __init__(self, *_, **__):
        self.services = {}

    def add_service(self, name: str):
        self.services[name] = {}

    def get_service_status(self, name: str):
        return self.services.get(name, {})

__all__ = ["ServiceMonitor"] 
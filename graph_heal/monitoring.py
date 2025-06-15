class ServiceMonitor:
    """No-op replacement used only for test import compatibility."""
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        """Pretend to start monitoring – does nothing."""
        return True

    def stop(self):
        """Pretend to stop monitoring – does nothing."""
        return True


class GraphUpdater:
    """Dummy graph updater that records calls for verification."""

    def __init__(self) -> None:
        self._updates = []

    # The real implementation might push updates to a DAG or message bus.
    # We just remember them so tests can inspect behaviour.
    def push(self, update):
        self._updates.append(update)

    def get_updates(self):
        return list(self._updates)


__all__ = ["ServiceMonitor", "GraphUpdater"] 
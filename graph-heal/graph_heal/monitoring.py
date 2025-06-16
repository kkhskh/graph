class ServiceMonitor:
    """Legacy no-op stub – the real monitoring system was removed."""
    def __init__(self, *_, **__):
        pass

    def start(self):
        """Pretend to start monitoring – does nothing."""
        return True

    def stop(self):
        """Pretend to stop monitoring – does nothing."""
        return True


class GraphUpdater:
    """Legacy no-op stub used only for import compatibility."""
    def __init__(self, *_, **__):
        pass

    # The real implementation might push updates to a DAG or message bus.
    # We just remember them so tests can inspect behaviour.
    def push(self, update):
        pass

    def get_updates(self):
        return []


__all__ = ["ServiceMonitor", "GraphUpdater"] 
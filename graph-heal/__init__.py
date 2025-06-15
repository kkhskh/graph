"""GRAPH-HEAL Python package root.

Exposes the current on-disk **snapshot schema version** and makes it explicit
for external tools so future migrations become trackable.
"""

__all__ = ["__schema__"]

#: JSON snapshot schema version written by capture_multiservice.py
__schema__: int = 1

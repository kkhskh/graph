"""Legacy shim – forwards everything to the real root package."""
from importlib import import_module as _imp, sys as _sys
_sys.modules[__name__] = _imp("graph_heal")

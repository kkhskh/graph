# Stub relocated from the legacy `graph-heal/scripts/` folder.
# See that file for full documentation.  We simply re-export the public
# surface so that import paths resolve regardless of where the evaluator
# lives in the repository.

from __future__ import annotations

import importlib as _il
import sys as _sys

# Prefer the already-loaded legacy implementation if present ----------------
_mod_name = "__legacy_adv_eval__"
if _mod_name in _sys.modules:
    _legacy = _sys.modules[_mod_name]
else:
    # Fallback: load the original stub implementation from the legacy path.
    _legacy = _il.machinery.SourceFileLoader(
        _mod_name,
        str((__file__).replace("graph_heal/scripts", "graph-heal/scripts")),
    ).load_module()
    _sys.modules[_mod_name] = _legacy  # cache for future imports

# Re-export everything public ------------------------------------------------
globals().update({k: v for k, v in vars(_legacy).items() if not k.startswith("__")})

__all__ = _legacy.__all__  # type: ignore[attr-defined] 
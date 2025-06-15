import importlib, pathlib, sys, types

# If a *top-level* ``scripts`` package exists (our repository root), extend this
# package's search path to include it.  This way, ``import scripts.foo`` works
# regardless of whether Python first found ``graph-heal/scripts`` or the root
# directory.

_root_scripts = pathlib.Path(__file__).resolve().parent.parent.parent / "scripts"

if _root_scripts.is_dir():
    # Make sure the directory is on ``sys.path`` so submodules can be discovered.
    sys.path.insert(0, str(_root_scripts))

    # Adopt the root *scripts* package if it is importable – this avoids having
    # two distinct modules called ``scripts`` which would confuse importers.
    try:
        _root_pkg = importlib.import_module("scripts")
        # Ensure the *root* directory is part of the package path available
        # for sub-module discovery.
        if str(_root_scripts) not in _root_pkg.__path__:
            _root_pkg.__path__.append(str(_root_scripts))

        # Replace the current module entry with the root one so they are the same
        sys.modules[__name__] = _root_pkg
    except Exception:  # pragma: no cover – root scripts absent or broken.
        # Fall back to making this very package search both directories.
        __path__.append(str(_root_scripts))

# Clean-up locals
del importlib, pathlib, sys, types, _root_scripts 
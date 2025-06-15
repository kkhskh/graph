import importlib, sys
# Point *any* import of graph_heal.graph_* back to the real package
_module = importlib.import_module("graph_heal")
sys.modules[__name__] = _module

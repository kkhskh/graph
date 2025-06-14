import sys, logging, importlib
import pytest

pytestmark = pytest.mark.skipif(sys.platform.startswith('linux'), reason="Root-only Linux behaviour not validated here")


def test_host_fault_noop(caplog):
    """The host_fault helper should warn and exit zero on non-Linux or non-root."""
    caplog.set_level(logging.WARNING)
    mod = importlib.import_module('graph_heal.tools.host_fault')
    rc = mod.main(['--cpu', '1'])
    assert rc == 0
    assert any('requires root privileges' in m for m in caplog.text.splitlines()) 
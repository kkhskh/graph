#!/usr/bin/env python3
"""Light-weight host-layer fault-injection helper.

Intended for future integration with *stress-ng* or similar tools.  For now it
behaves as a safe stub so unit tests and CI can exercise the command-line
interface regardless of platform or privileges.

Examples
--------
$ python3 graph-heal/tools/host_fault.py --cpu 4 --mem 2G  # real injection
$ python3 graph-heal/tools/host_fault.py                   # uses defaults

When executed on anything other than *Linux* **as root** the script logs a
warning and exits *successfully* so callers can continue their pipelines.
"""
from __future__ import annotations

import argparse
import logging
import os
import platform
import subprocess
import sys
from typing import List

logger = logging.getLogger("host_fault")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _is_root() -> bool:
    """Return *True* if the current process runs with UID 0 (root)."""
    return hasattr(os, "geteuid") and os.geteuid() == 0  # type: ignore[attr-defined]


def _build_stress_cmd(cpu: int, mem: str) -> List[str]:
    """Return a *stress-ng* command line matching *cpu* and *mem* settings.

    The memory string is passed verbatim – validation is postponed until we
    add real execution logic.
    """
    return [
        "stress", "--cpu", str(cpu), "--vm", "1", "--vm-bytes", mem, "--timeout", "30s"
    ]


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:  # noqa: C901 – intentionally simple
    p = argparse.ArgumentParser(description="Inject synthetic CPU / memory load on the host machine.")
    p.add_argument("--cpu", type=int, default=2, help="Number of CPU workers to spawn (default: 2)")
    p.add_argument("--mem", default="1G", help="Total memory stress e.g. 512M / 1G (default: 1G)")
    args = p.parse_args(argv)

    if platform.system().lower() != "linux" or not _is_root():
        logger.warning("Host fault injection requires root privileges on Linux – stubbed no-op")
        return 0

    cmd = _build_stress_cmd(args.cpu, args.mem)
    logger.info("Executing host fault: %s", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        logger.error("'stress' command not found – please install stress-ng")
        return 1
    except subprocess.CalledProcessError as exc:
        logger.error("stress command failed with exit code %s", exc.returncode)
        return exc.returncode

    logger.info("Host fault injection complete")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main()) 
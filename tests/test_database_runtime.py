from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_database_runtime_registration_is_explicit_and_idempotent() -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = """
from keycan.data.database import Database
assert not hasattr(Database, "managed_groups")
import keycan.data.database_runtime
assert not hasattr(Database, "managed_groups")
from keycan.data.database_runtime import install_database_runtime
install_database_runtime()
assert hasattr(Database, "managed_groups")
registered = Database.managed_groups
install_database_runtime()
assert Database.managed_groups is registered
"""
    subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )

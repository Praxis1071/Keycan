from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_managed_database_is_an_explicit_subclass_without_runtime_patching() -> None:
    project_root = Path(__file__).resolve().parents[1]
    script = """
from keycan.data.database import Database
assert not hasattr(Database, "managed_groups")
from keycan.data.managed_database import ManagedDatabase
from keycan.data.database_runtime import ManagedDatabase as CompatibilityManagedDatabase
assert not hasattr(Database, "managed_groups")
assert issubclass(ManagedDatabase, Database)
assert CompatibilityManagedDatabase is ManagedDatabase
assert hasattr(ManagedDatabase, "managed_groups")
assert hasattr(ManagedDatabase, "export_data")
assert hasattr(ManagedDatabase, "restore_defaults")
"""
    subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )

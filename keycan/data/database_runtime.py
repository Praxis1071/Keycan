"""Backward-compatible import for the managed database implementation.

New application code should import :class:`ManagedDatabase` from
:mod:`keycan.data.managed_database`.
"""

from keycan.data.managed_database import ManagedDatabase

__all__ = ["ManagedDatabase"]

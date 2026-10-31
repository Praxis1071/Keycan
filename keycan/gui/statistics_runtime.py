"""Compatibility import for the former statistics runtime patch.

MetricCard now owns its animation lifecycle directly in statistics_clean.py.
Importing this module is intentionally side-effect free.
"""

from keycan.gui.statistics_clean import MetricCard

__all__ = ["MetricCard"]

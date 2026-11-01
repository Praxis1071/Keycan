> Archived on 2026-11-01. This document is retained for historical context only and is not an active implementation plan. The current plan is [ROADMAP.md](../../ROADMAP.md), with technical details in [ARCHITECTURE_REFACTOR_ROADMAP.md](../ARCHITECTURE_REFACTOR_ROADMAP.md) and [ARCHITECTURE_REFACTOR_STRATEGY.md](../ARCHITECTURE_REFACTOR_STRATEGY.md).

---

# Keycan Architecture Refactor Plan

This document tracks the planned project structure modernization.

Goals:
- Reduce main.py responsibility.
- Separate GUI, application logic and data systems.
- Prepare for responsive GTK4/libadwaita UI.
- Prepare for Dashboard, user databases, statistics, XP and future features.

Migration will be incremental to avoid breaking the working 2.1.0 release.

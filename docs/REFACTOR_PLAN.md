# Keycan Architecture Refactor Plan

This document tracks the planned project structure modernization.

Goals:
- Reduce main.py responsibility.
- Separate GUI, application logic and data systems.
- Prepare for responsive GTK4/libadwaita UI.
- Prepare for Dashboard, user databases, statistics, XP and future features.

Migration will be incremental to avoid breaking the working 2.1.0 release.

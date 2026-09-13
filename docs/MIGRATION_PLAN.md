# Keycan Refactor Migration Plan

## Goal

Move Keycan toward a modular GTK4 + libadwaita architecture without changing the current user experience or breaking the stable 2.1.0 release.

## Safety Rules

- Keep a backup branch before every major migration step.
- Make small isolated changes.
- Test application startup after each migration.
- Do not rewrite working features unnecessarily.

## Target Structure

```
keycan/
├── gui/
│   ├── workspace.py
│   ├── sidebar.py
│   ├── settings.py
│   └── dashboard.py
├── core/
│   ├── typing.py
│   ├── statistics.py
│   ├── database.py
│   └── progress.py
├── models/
└── services/
```

## Migration Order

1. Create architecture folders.
2. Move independent GUI components.
3. Separate settings UI.
4. Separate workspace UI.
5. Separate statistics and future progress systems.
6. Introduce responsive navigation architecture.

## Non Goals

- No redesign of the core typing workflow.
- No removal of existing features.
- No breaking changes during migration.

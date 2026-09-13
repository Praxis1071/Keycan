# Keycan Refactor Migration Map v1

## Goal

Move Keycan toward a modular GTK4/libadwaita architecture while preserving the working 2.1.0 behavior.

## Rules

- Do not change user-facing behavior during file migrations.
- Make small commits.
- Test application startup after each migration.
- Keep backup points before risky changes.

## Planned Migration

| Current area | Target location | Priority |
| --- | --- | --- |
| Application startup | `keycan/app.py` | High |
| Search widgets | `keycan/gui/search.py` | First |
| Settings UI | `keycan/gui/settings.py` | Second |
| Main workspace UI | `keycan/gui/workspace.py` | Third |
| Typing calculations | `keycan/core/typing.py` | Fourth |
| Statistics and speed tracking | `keycan/core/statistics.py` | Fifth |
| User sources/database | `keycan/core/database.py` | Future |
| Progress system | `keycan/core/progress.py` | Future |

## Target Architecture

```
keycan/
├── gui/
├── core/
├── models/
├── services/
└── utils/
```

## Current First Migration

The first component planned for extraction is `SourceSearchDropdown` from `main.py` into `keycan/gui/search.py`.

Reason:

- Low risk
- Independent component
- Allows testing the new architecture before larger migrations

# Keycan Architecture Refactor Strategy

This document is the implementation companion to `ROADMAP.md` Stage 10. The roadmap is the authoritative task checklist; this document records technical decisions and migration safeguards.

## 1. Current architecture findings

The repository already has a useful separation between `app.py`, `window.py`, `gui/`, `data/`, `services/`, `core/`, and `utils/`. The remaining challenge is clear ownership and small, testable boundaries between the existing modules.

Confirmed findings from the current branch:

- `keycan/app.py` no longer performs database runtime registration.
- `managed_database.py` exposes a concrete `ManagedDatabase(Database)` subclass. The previous runtime assignment of methods onto the base class has been removed; content CRUD, progression queries, default-content snapshots, and JSON backup import/export are available through the subclass.
- `database_runtime.py` is now a small backward-compatible re-export; active application code imports `ManagedDatabase` from `managed_database.py`.
- The base `Database` class remains unchanged when `database_runtime.py` is imported. A subprocess regression test protects this boundary.
- `database.py` already contains overlapping database behavior and schema migrations. The two files must be compared method-by-method before consolidation.
- `window.py` imports and coordinates the database, workspace, search, settings, statistics, profile, keyboard guide, translation, and preference components. It also owns substantial interaction state.
- The active GUI imports `settings2.py` and `statistics_clean.py`. The older `settings.py` and `statistics.py` now re-export the active classes to preserve their historical import paths without maintaining duplicate implementations.
- The former statistics runtime patch has been removed from the active application path; the animation behavior now belongs to `MetricCard`.
- The current backup format is already JSON (version 3), with stable identifiers and compatibility handling. It must be preserved and strengthened rather than replaced with a second unrelated format.
- The initial CI baseline exposed `test_backup_round_trip_preserves_deleted_lesson_history`. The root cause was JSON `null` identities being converted to the literal string `None`, which selected the wrong identity-matching path. The importer now normalizes null identities before matching, and the full CI suite passes.

These findings are an initial map, not permission to delete modules. Full import/reference checks and method-level comparisons remain mandatory.

## 2. Target responsibilities

- **Packaged default lessons:** version-controlled JSON files under `keycan/resources/lessons/<language>/`.
- **Custom user-created lessons and user edits:** retain the existing SQLite-backed editing model. Do not migrate this mutable user data to JSON without a separately justified and approved design.
- **User progress and history:** SQLite, including practice sessions, statistics inputs, profile progression and stable lesson references.
- **Backup/restore:** versioned JSON export/import. A backup includes custom content and user history; it is not the live application database.
- **Lesson access:** one `LessonService` API. GUI components must not know whether a lesson came from packaged JSON or a custom-content repository.
- **Database access:** explicit data/repository methods; no GUI SQL and no import-time monkey-patching.
- **Typing engine:** unchanged and outside the refactor scope.

The first migration should move the built-in/default catalog to JSON without forcing custom-content CRUD or historical practice records into a new persistence model. If later evidence shows that custom content also needs a JSON runtime store, that is a separate design decision with a tested identity and migration strategy—not an incidental side effect.

## 3. Lesson JSON contract

The JSON schema must be explicit and versioned. It should include a schema version, language, stable group identifier, concise display name, and ordered lessons with stable identifiers and text. Runtime validation must reject malformed structures, duplicate identifiers, empty groups, and empty lesson text with a useful error.

Content normalization rules:

- Turkish letters (`çğıöşü` and uppercase equivalents) are valid letters and must be preserved.
- Group names should contain letters and word-separating spaces only; remove numbering, punctuation, decorative labels, and redundant wording.
- Lesson text should contain letters and normal whitespace only after cleanup. Remove digits and punctuation from the prepared catalog, collapse repeated whitespace, and preserve word order.
- Do not silently discard words or rewrite lesson meaning. Numeric tokens that carry instructional meaning must be reviewed manually before removal.
- Keep the original catalog snapshot in version control until the cleaned catalog passes comparison and content-quality checks.
- Lesson IDs must be stable across title cleanup and text normalization so historical records do not become detached from their lessons.

## 4. Migration sequence

### Gate A — establish a reliable baseline
1. Fix the existing backup regression and add/retain a focused test.
2. Run the complete test suite and static checks.
3. Record current table counts, default group/lesson counts, IDs, and history references before changing data sources.

### Gate B — define and validate JSON
1. Add the JSON schema and loader without changing the current GUI path.
2. Add unit tests for valid catalogs, invalid schema, duplicate IDs, Turkish letters, whitespace normalization, and missing files.
3. Export the current default content into candidate JSON files.
4. Review group names and lesson text, then run automated content audits.

### Gate C — switch default lessons safely
1. Implement `LessonService` as the only public API for listing groups, listing lessons, and retrieving lesson text.
2. Add a temporary compatibility adapter so existing consumers can use the new service without a large simultaneous GUI rewrite.
3. Compare JSON catalog identities against the existing SQLite default content and preserve stable lesson identifiers.
4. Switch default-content reads to JSON only after tests prove identical ordering and intended cleaned text.
5. Preserve custom-content CRUD in SQLite and preserve existing JSON backup import/export.

### Gate D — simplify the architecture
1. Replace runtime monkey-patching with explicit methods or composed services.
2. Consolidate duplicate database and statistics implementations only after proving which methods are active.
3. Keep one settings implementation and one statistics implementation; compatibility modules should remain thin re-exports rather than duplicate implementations.
4. Extract page orchestration and event coordination from `window.py` into focused controllers/services only where there is a real responsibility boundary.
5. Keep `window.py` as a small composition root for the application window.

### Gate E — data and regression hardening
1. Keep SQL schema migrations explicit, transactional, and backward compatible.
2. Ensure history snapshots remain readable if a default lesson is renamed, cleaned, removed, or unavailable.
3. Validate JSON backups before importing; import atomically and roll back on malformed content.
4. Preserve stable session IDs and idempotent import behavior.
5. Test clean install, existing database upgrade, restore defaults, reset content, custom content CRUD, backup round-trip, and deleted-content history.

## 5. Non-negotiable safety rules

- Never modify `keycan/core/typing_engine.py` during this work.
- Never delete the existing database, lesson catalog, or backup until a verified replacement and recovery path exist.
- Do not rewrite the whole application.
- Do not add Rust, new frameworks, or abstraction layers without a measured need.
- Make one coherent change per commit. Future implementation work should use a dedicated refactor branch; documentation corrections may be committed directly to main when explicitly requested.
- A phase is complete only when its tests pass and existing features are checked.
- If tests cannot be executed in the current environment, report that limitation; do not claim they passed.

## 6. Initial content audit

The current default catalog contains 82 active groups and 1,833 lessons. A first-pass audit counted approximately 12,963 numeric characters and 23,070 punctuation/symbol characters in default lesson text. Turkish and other Unicode letters account for the remaining letter content; all whitespace should be normalized rather than removed.

A mechanical group-name cleanup creates collisions (for example, the F/Q keyboard variants, groups distinguished by the number of matching initial letters, multiple tekerleme parts, and several date-based KM collections). Therefore group names must be reviewed with a unique-name check; a blind regex cleanup is not acceptable. Preserve group and lesson IDs/order while changing visible names and lesson text.

## 7. Work completed and present on main

- Added `keycan/resources/lessons/tr/catalog.json` with schema version 1, 82 uniquely named groups, and 1,833 lessons. Each group also carries its exact bundled `legacy_name` so the service can distinguish a legacy label from a user rename.
- Added `keycan/services/lesson_catalog.py` to load and validate the packaged catalog without GTK or third-party dependencies.
- Added `keycan/services/lesson_service.py` as a read-only compatibility bridge between the packaged catalog and SQLite.
- Routed the main typing window and the lesson-content manager's read operations through `LessonService`. Existing SQLite write operations remain unchanged.
- The service displays cleaned JSON names/text when the database still contains the original bundled content. If a user has renamed a group or edited a lesson, the service keeps the SQLite value instead.
- Compared all 1,833 catalog lesson texts against the tracked database export. After applying the exact letter-preserving cleanup normalization, every lesson matched: no words were added, lost, or reordered. The lesson IDs and per-group order also match exactly. Turkish and other Unicode letters are preserved.
- Compared all 82 group IDs and 1,833 lesson IDs. The catalog covers every bundled default ID. A stale deleted empty source (ID 69) is intentionally not treated as catalog content.
- Added service tests for full catalog coverage, all lesson-text overlays, unchanged SQLite rows, user renames/edits, custom groups/lessons, and SQLite fallback when the JSON resource is missing or invalid. In fallback mode the service delegates directly to the existing database API, preserving the previous ordering and labels.
- Added an in-app status warning and English translation for catalog fallback. A missing or malformed packaged JSON file no longer prevents the application from opening.
- The catalog already contains many repeated texts across different groups. The cleanup introduces one additional duplicate cluster of four lessons: two legacy labels (YARGITAY 16-A and 18-A) collapse to the same letter-only text, repeated in the current and previous Yargıtay groups. All four lesson IDs and positions are retained; no lesson was removed.
- Curated unique group names rather than relying on a blind regex. F/Q keyboard variants and other similar groups remain distinguishable without digits or punctuation.
- Fixed the JSON backup null-identity bug. The tracked database is copied to a temporary location for migration/integrity checks; the repository database is not modified.
- Latest GitHub Actions run: all five jobs passed, including the GTK/Xvfb smoke test.

**Current migration boundary:** The GUI now reads built-in display names and unchanged lesson text from JSON through `LessonService`, while SQLite continues to hold the editable workspace, custom content, ordering/deletion state, and history. This is a deliberate compatibility phase, not a destructive database migration. No SQLite tables or old files have been removed. The next gate is to harden JSON error handling and verify restore/reset/backup round trips against the new service before any database responsibilities are consolidated.

## 8. Dependency and runtime map

- `main.py` delegates to `keycan.app.main()`.
- `app.py` imports the composed window without a database registration side effect. `statistics_runtime.py` is no longer part of the active application import path.
- `KeycanWindow` uses `ManagedDatabase`, an explicit subclass of the base `Database` class. Importing `database_runtime.py` does not modify the base class.
- The managed database constructor first runs the base schema migrations in `database.py`; it then migrates custom paths, creates/loads default-content snapshots, and reconciles the snapshot with active content.
- Tests that need content management, progression, or backup methods instantiate `ManagedDatabase`; tests that need only base statistics/schema behavior can continue using `Database`.
- The Flatpak wrapper seeds the user's XDG data database from the packaged database. The Flatpak manifest copies the entire `keycan/` package, so the new JSON resource is included automatically.
- `window.py` and `content_manager2.py` route group/lesson reads and display-name formatting through `LessonService`; content writes and statistics persistence remain in SQLite through `ManagedDatabase`.
- The active GUI modules are `settings2.py` and `statistics_clean.py`. The older `settings.py` and `statistics.py` are now thin compatibility re-exports, preserving old import paths without duplicating their implementations.
- The former `statistics_runtime.py` patch only replaced `MetricCard.set_value` to cancel stale GLib animation timers. That behavior now lives directly in `MetricCard`; the runtime file remains as a side-effect-free compatibility import, and `app.py` no longer imports it.
- `database.py` still contains older custom-content CRUD methods alongside the richer managed API. `ManagedDatabase` intentionally overrides the application-facing operations while preserving inherited legacy methods. A method-by-method call-site and external compatibility audit is still needed before any duplicate methods are removed. Managed methods are now ordinary class methods.

### Consequence for the next implementation step

The JSON catalog is read through `LessonService`; GUI consumers do not read JSON directly. Both the main window and content manager use the service for group/lesson reads and display formatting. User writes remain in SQLite. A future improvement may add a clearer user-facing warning when the packaged JSON catalog is invalid; do not switch write ownership or remove SQLite snapshots.

## 9. Database and CI validation findings

- The repository contains both `typing_data.db` and the 10 MB JSON database export. The JSON export was read through the Git object API; the binary database was not modified.
- The checked-in database is not guaranteed to have the latest runtime schema before migrations. The original `check.sh` assumed migrated columns already existed and failed against the clean repository database.
- `check.sh` now copies the tracked database to a temporary directory, applies the real `Database` migrations to that copy, and performs integrity/schema/snapshot checks there. This validates migrations without mutating the checked-in database.
- The check also verifies that all group and lesson IDs in the packaged JSON catalog match the default-content snapshot IDs in the migrated database.
- Current repository database validation reports 83 active sources (82 built-in groups plus one active custom group) and 1,833 active lessons.
- The full CI workflow runs `check.sh`, Ruff's undefined-name check, the full pytest suite, and an Xvfb GTK smoke test. Latest successful run: [41299278251](https://github.com/Praxis1071/Keycan/actions/runs/41299278251); 52 focused checks, 72 pytest tests, Ruff F821, and GTK window/session/persistence/retry smoke test all passed.


## 10. Duplicate-module audit update (historical findings, updated below)

- Confirmed that `settings2.py` and `statistics_clean.py` are the active GUI implementations. The older `settings.py` and `statistics.py` are thin compatibility re-exports, not separate implementations.
- Moved the metric-card animation cancellation/reset logic into `MetricCard.set_value`. The former `statistics_runtime.py` file remains as a side-effect-free compatibility import, and the application no longer imports it.
- The database runtime registration mechanism has been removed. All managed operations are now ordinary methods declared directly in `ManagedDatabase`; no module-level function assignments remain.
- `window.py` now exposes one public `KeycanWindow` class composed over a private base class. The duplicate source-loading override and runtime class alias have been removed.


## 11. Managed database subclass refactor (branch: architecture/maintenance-refactor)

- Replaced the previous `install_database_runtime()` monkey-patch with `ManagedDatabase(Database)` in `managed_database.py`.
- Kept `database_runtime.py` as a small compatibility re-export; active application code imports the dedicated managed module.
- The application window now constructs `ManagedDatabase`; `app.py` no longer registers methods or depends on import order.
- The base `Database` class remains unchanged when the managed module is imported.
- Content management, default snapshots, progression summary, and backup/restore methods remain available on `ManagedDatabase`.
- Updated custom-content, lesson-service, and progression tests to use the managed subclass.
- Added a subprocess test proving the base class is not mutated and the managed API is available.
- Extracted typing-session metrics from `window.py` into pure `core/session_metrics.py` calculations and added focused tests.
- Moved editor privacy presentation and result highlighting from the application window into `gui/workspace.py`, which already owns the two text views.
- Fixed a completion-status reference uncovered during the extraction and added an Xvfb-based GTK smoke test that constructs the real window and completes a persisted practice session.
- GitHub Actions run 41299278251 passed all five jobs: 52 `check.sh` checks, 72 pytest tests, Ruff F821, and GTK/Xvfb launch/session/persistence/retry smoke test.
- The latest smoke test also exercises the settings content manager, privacy tag toggling, live language switch and failed-save retry with stable session identity.
- Full interactive human verification on the user's desktop remains a separate final gate.



## 12. Current data ownership decisions (2026-11-01)

This section supersedes any older wording in this document that suggests all user lesson content must move to JSON.

- Packaged built-in lesson catalog: version-controlled JSON under keycan/resources/lessons/.
- User-created groups, editable content, ordering/deletion state and personal changes: retain the current SQLite-backed model.
- Practice sessions, statistics inputs, profile-derived progress and history: SQLite.
- Backup/restore: keep the existing versioned JSON export/import format as a portable backup contract. It is not the live store for user content.
- LessonService: the GUI-facing read boundary for packaged built-in lessons. User content writes continue through the existing database layer unless a future, separately approved architecture decision changes that.
- No database tables, user content stores or backup formats are to be removed merely to achieve a JSON-first design.

### Verified stabilization update

The stabilization pull request [#2](https://github.com/Praxis1071/Keycan/pull/2) was merged into main on 2026-10-31 (merge commit 3c5c80180c3d911696903a61868abffd43a7b2df). Its validation report records 45 passing tests and successful Stage 5, Stage 6, Stage 7 and full regression jobs. Manual GTK checks remain a separate requirement; CI success is not evidence that desktop interactions were manually verified.

### Remaining high-risk work

- Audit overlapping legacy CRUD methods inherited from `Database`; retain them until external compatibility and all call sites are established.
- Continue extracting session timing and lesson selection from `window.py` only where a small independent responsibility can be tested without moving GTK widget work off the main thread. Session persistence/retry is now handled by `SessionRecorder`.
- `window.py` still coordinates multiple pages and typing-session state. The workspace now owns editor privacy and result presentation; preserve GTK signal/lifecycle behavior in any further extraction.
- Legacy settings/statistics module paths are retained as compatibility re-exports; their implementations now have one authoritative source.
- Backup restore, reset/restore defaults and historical session identity must remain regression-gated.

# Keycan Architecture Refactor Strategy

This document is the implementation companion to `ROADMAP.md` Stage 10. The roadmap is the authoritative task checklist; this document records technical decisions and migration safeguards.

## 1. Current architecture findings

The repository already has a useful separation between `app.py`, `window.py`, `gui/`, `data/`, `services/`, `core/`, and `utils/`. The problem is not a lack of folders; it is unclear ownership and runtime patching across modules.

Confirmed findings from the current branch:

- `keycan/app.py` imports `database_runtime` and `statistics_runtime` only for their import-time side effects.
- `database_runtime.py` replaces many `Database` methods after class creation. It contains custom content CRUD, progression queries, default-content snapshots, and JSON backup import/export.
- `database.py` already contains overlapping database behavior and schema migrations. The two files must be compared method-by-method before consolidation.
- `window.py` imports and coordinates the database, workspace, search, settings, statistics, profile, keyboard guide, translation, and preference components. It also owns substantial interaction state.
- The active GUI imports `settings2.py` and `statistics_clean.py`. The older `settings.py` and `statistics.py` have no direct references in the current code-search results, but must be checked for indirect imports and tests before removal.
- `statistics_runtime.py` monkey-patches `MetricCard.set_value` from `statistics_clean.py`.
- The current backup format is already JSON (version 3), with stable identifiers and compatibility handling. It must be preserved and strengthened rather than replaced with a second unrelated format.
- The current CI baseline has one failing regression: `test_backup_round_trip_preserves_deleted_lesson_history`. The failure occurs because a failed default-source identity match prevents the importer from trying the legacy source-ID-plus-name fallback. This must be corrected before content migration.

These findings are an initial map, not permission to delete modules. Full import/reference checks and method-level comparisons remain mandatory.

## 2. Target responsibilities

- **Packaged default lessons:** version-controlled JSON files under `keycan/resources/lessons/<language>/`.
- **Custom user-created lessons:** retain the existing SQLite-backed editing model initially. These are mutable user data, not application resources.
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
3. Keep one settings implementation and one statistics implementation; remove legacy copies only after import, test, and packaging references are updated.
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
- Make one coherent change per commit and keep all work on the dedicated refactor branch.
- A phase is complete only when its tests pass and existing features are checked.
- If tests cannot be executed in the current environment, report that limitation; do not claim they passed.

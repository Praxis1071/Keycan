# Keycan Backup and Data Safety Policy

This policy applies to application data, database changes, catalog changes, and architecture work.

## Current release baseline

- Current stable release: **Keycan 2.5.0**
- Release reference: [v2.5.0](https://github.com/Praxis1071/Keycan/releases/tag/v2.5.0)
- The release is a reference point, not a substitute for backing up the current working tree and user data before risky operations.

Do not rely on an old fixed backup branch name. Create a clearly named backup branch or tag for each significant migration, based on the exact commit being protected.

## Before structural or data changes

1. Confirm the working tree and current branch; do not overwrite unrelated user changes.
2. Create a Git backup point for source changes.
3. Back up the actual user database and any user-managed content separately from the source repository.
4. Verify that the backup can be read and that its size/content is plausible.
5. Record database integrity, schema version, row counts, stable IDs, and history references before migration.
6. Keep a tested rollback path until the new implementation has passed the complete regression suite and manual application checks.

## Migration rules

- Never edit the user's only database copy during analysis or migration testing.
- Perform experiments on temporary copies.
- Use transactions for SQLite changes and atomic replacement for JSON files.
- Validate imports and backups before writing them.
- Preserve stable lesson/session identities and historical snapshots.
- Do not delete old tables, files, or compatibility code until replacement behavior and recovery have been verified.
- Make small, focused commits that can be reverted independently.
- If validation fails, stop and restore the previous known-good state.

## Completion requirements

A data migration is complete only when:

- Source and destination record counts and stable identities have been compared.
- Practice history and profile-derived values remain consistent.
- Backup and restore round-trip tests pass.
- Existing database upgrade and clean-install paths pass.
- The full automated test suite passes.
- The application has been opened and its critical workflows manually checked.

**Stability and user-data preservation take priority over architectural preference or implementation convenience.**

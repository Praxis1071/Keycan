# Keycan Backup Policy

## Before major changes

Create a backup point/branch before structural migrations.

Current stable reference:

```
Keycan 2.1.0
```

Backup branch:

```
backup/v2.1.0-before-refactor
```

## Migration rules

1. Keep the last stable release untouched.
2. Apply migrations incrementally.
3. Test application launch after each stage.
4. Do not delete old working code until the replacement is verified.
5. Keep commits small and easy to revert.

## Refactor philosophy

Stability first. Architecture improvements must preserve the existing user experience and reliability.

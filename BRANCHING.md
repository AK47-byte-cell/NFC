# Git Branching Strategy

This project uses a lightweight GitFlow-style workflow to keep work organized without too much process overhead.

## Long-lived branches

- `main`: production-ready, stable releases only.
- `develop`: integration branch for upcoming work.

## Short-lived branches

Create these from `develop` unless noted otherwise.

- `feature/<area>-<short-desc>`
  - For new functionality.
  - Example: `feature/gui-batch-progress`
- `fix/<area>-<issue>`
  - For non-urgent bug fixes.
  - Example: `fix/scripts-context-menu-quote-handling`
- `chore/<task>`
  - For maintenance/refactors/dependency updates.
  - Example: `chore/deps-upgrade`
- `docs/<topic>`
  - For documentation-only changes.
  - Example: `docs/offline-deployment-guide`
- `release/vX.Y.Z`
  - Cut from `develop` when preparing a release.
- `hotfix/vX.Y.Z-<issue>`
  - For urgent production fixes, branched from `main`.

## Suggested area tags for this repo

- `gui`
- `core`
- `scripts`
- `packaging`
- `docs`
- `infra`

Examples:

- `feature/gui-dragdrop-reorder`
- `fix/core-ffmpeg-detection`
- `chore/packaging-pyinstaller-cleanup`
- `docs/readme-setup-clarity`

## PR and merge flow

1. Create your branch from `develop`.
2. Open a PR back into `develop`.
3. For a release, create `release/vX.Y.Z` from `develop` and validate.
4. Merge release into both `main` and `develop`.
5. For urgent production bugs, branch `hotfix/*` from `main` and merge back into both `main` and `develop`.

## Quick commands

```bash
git checkout develop
git pull
git checkout -b feature/gui-batch-progress
```

```bash
git checkout main
git pull
git checkout -b hotfix/v1.3.1-crash-on-long-audio
```

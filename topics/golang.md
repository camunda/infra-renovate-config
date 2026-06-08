# golang (.tool-versions)

## Status
- Automerge: patch AND minor already configured centrally — `golang` is listed in both the patch and minor `matchPackageNames` blocks, plus `matchCategories: ["golang"]` patch/minor rules in `default.json5`.
- Pinned version: none.

## Gotchas
- asdf-managed toolchain in repo-root `.tool-versions`. No kustomize build to validate; routine patch toolchain bumps are safe.
- These PRs surface on the maintenance board even though they're automerge-eligible; with `platformAutomerge: false`, Renovate merges them itself on its next run once required checks are green. No manual action needed.

## Upgrade log
| Date | Version | Outcome | PR |
|------|---------|---------|----|
| 2026-06-08 | 1.26.3 → 1.26.4 | checks green, automerge-eligible, confirmed safe | #13050 |

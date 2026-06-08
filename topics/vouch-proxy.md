# vouch-proxy

## Status
- Automerge: patch enabled centrally (`/vouch/vouch-proxy/` in patch list). Minor NOT automerged — review required.
- Pinned version: none.

## Build / apply
- Base: `camunda-int/kustomize/base/vouch/vouch/kustomization.yml` (image-tag only via `images:`).
- Build: `make vouch` in `camunda-int/kustomize/dev`.
- Apply: `make apply-non-interactive vouch` (int-dev) — two deployments: `vouch-camunda-cloud` + `vouch-int-camunda-com`.

## Gotchas
- `quay.io/vouch/vouch-proxy` does NOT publish GitHub releases. Use tag comparison for changelog:
  `gh api /repos/vouch/vouch-proxy/compare/v<old>...v<new> --jq '.commits[].commit.message'` (tags are `v`-prefixed).
- Config comes from the `vouch-config-*` ExternalSecret; image bumps don't touch it.

## Upgrade log
| Date | Version | Outcome | PR |
|------|---------|---------|----|
| 2026-06-08 | 0.47.2 → 0.48.0 | clean build + applied to int-dev; multipart-cookie bugfix; no config changes | #13076 |

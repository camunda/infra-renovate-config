# actions-runner-controller (gha-runner-scale-set)

## Status
- Automerge: patch enabled centrally (`/infra-actions-runner/`, `ghcr.io/actions/actions-runner` in the patch list).
- Pinned version: none.

## Build / apply
- Base: `kustomize/base/actions-runner/controller/upstream-helm-base/` (shared by camunda-ci and camunda-ci-eks).
- Build: `make actions-runner-controller` in `camunda-ci/kustomize/dev`.
- Apply: `make apply-non-interactive actions-runner-controller` (ci-dev) — applies deployment, CRDs, RBAC, namespace cleanly.

## Gotchas
- Renovate regenerates `controller.yml` + `values.upstream.yml`. The `values.upstream.yml` additions are reference-only (e.g. pprof, workqueue rate limiter docs) and are NOT wired into our `values.yml`.
- Patch bumps so far change only version labels + image tags in the rendered manifest.

## Upgrade log
| Date | Version | Outcome | PR |
|------|---------|---------|----|
| 2026-06-08 | 0.14.1 → 0.14.2 | clean build + applied to ci-dev; bugfix (novolume SA) + runner v2.334.0; no CRD/breaking | #12869 |

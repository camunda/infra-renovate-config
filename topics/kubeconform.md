# kubeconform

## Status
- Automerge: NOT yet configured. **Patch-automerge candidate** — suggested adding `yannh/kubeconform` to the patch list in central `default.json5`.
- Pinned version: none.

## Where used
- CI manifest validation only: `cmd/k8s/gha-diff-scripts/manifest-validation.sh` (invoked by `.github/workflows/kubernetes-diff.yml`). Installed from repo-root `.tool-versions`.
- Flags used: `-schema-location`, `-skip`, `-kubernetes-version`, `-summary`. Watch for CLI-flag changes across majors.

## Gotchas
- Every bump is fully exercised by the PR's own `Manifest generation and diff` checks across ALL clusters (ci, ci-eks, int, pub × prod/stage). Green checks == kubeconform validated every generated manifest. Strong safety signal; no manual build needed.

## Upgrade log
| Date | Version | Outcome | PR |
|------|---------|---------|----|
| 2026-06-08 | 0.7.0 → 0.8.0 | validated via all-cluster manifest-diff checks; bugfixes + openapi2jsonschema-go; no flag changes | #13069 |

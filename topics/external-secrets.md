# external-secrets (ESO)

## Status
- Automerge: patch enabled centrally (`/external-secrets/` in patch list). Minor NOT automerged — review required.
- Pinned version: none.

## Build / apply
- Base: `kustomize/base/external-secrets-operator/` (update.sh + `upstream-helm-base/eso.yml`). Shared across all projects.
- Build: `make external-secrets` in `camunda-ci/kustomize/dev`.
- Apply: `make apply-non-interactive external-secrets` (ci-dev) — applies deployment, RBAC, and `ClusterSecretStore/vault-backend`.

## Gotchas
- We consume ESO exclusively via the **Vault** `ClusterSecretStore` (`vault-backend`). Provider-specific changes (Kubernetes TokenRequest, GCP/keeper/passbolt, etc.) do not affect us.
- Our rendered `eso.yml` for minor bumps changed only image tag + version labels — no CRD schema or RBAC drift. (Confirm CRDs separately if a release lists CRD changes.)
- ESO is on the v2.x line (chart `external-secrets-2.x`).

## Upgrade log
| Date | Version | Outcome | PR |
|------|---------|---------|----|
| 2026-06-08 | 2.5.0 → 2.6.0 | clean build + applied to ci-dev; feature/fix minor; Vault path unaffected | #13067 |

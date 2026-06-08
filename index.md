# Maintenance DRI Memory — Index

Persistent cross-run memory for the Maintenance DRI automation handling Renovate
PRs in `camunda/infra-core`. One file per topic under `topics/`.

| Topic | File | Summary | Last updated |
|-------|------|---------|--------------|
| actions-runner-controller | [topics/actions-runner-controller.md](topics/actions-runner-controller.md) | Patch bumps clean; image+label only in our overlay; patch automerge already configured | 2026-06-08 |
| golang (.tool-versions) | [topics/golang.md](topics/golang.md) | asdf toolchain; patch+minor automerge already configured centrally | 2026-06-08 |
| external-secrets | [topics/external-secrets.md](topics/external-secrets.md) | v2.x minor bumps clean; we use Vault ClusterSecretStore only | 2026-06-08 |
| kubeconform | [topics/kubeconform.md](topics/kubeconform.md) | CI-only validation tool; fully exercised by manifest-diff checks; patch-automerge candidate | 2026-06-08 |
| vouch-proxy | [topics/vouch-proxy.md](topics/vouch-proxy.md) | camunda-int; image-tag only; no GitHub releases (use tag compare) | 2026-06-08 |
| nexus | [topics/nexus.md](topics/nexus.md) | StatefulSet; minor bumps add formats + behavioral security changes; watch auth rate-limit & PyPI chained-proxy issue | 2026-06-08 |

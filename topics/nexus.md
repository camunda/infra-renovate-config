# nexus (sonatype/nexus3)

## Status
- Automerge: patch enabled centrally (`/sonatype/nexus3/` in patch list). Minor NOT automerged — review required.
- Pinned version: none.

## Build / apply
- Base: `camunda-ci/kustomize/base/nexus/nexus/kustomization.yml` (image-tag only; also pins `alpine`).
- Build: `make nexus` in `camunda-ci/kustomize/dev`.
- Apply: `make apply-non-interactive nexus` (ci-dev) — **StatefulSet** `repository-ci-camunda-cloud` (HA, replicas 0/1). Pod roll runs the on-startup DB migration (one-way; fine on dev).

## Gotchas / behavioral changes to watch on minor bumps
- Release notes live at `help.sonatype.com/en/sonatype-nexus-repository-<ver>-release-notes.html` (no GitHub release).
- **3.93.0:** auth rate limiting ON by default (HTTP 429 after 3 consecutive failed auths; tunable `nexus.auth.ratelimit.*`; UI-only when SSO absent). Correctly-credentialed CI unaffected.
- **3.93.0:** IP Allow List on by default — Pro/Cloud only, existing config preserved. No impact if OSS/Community.
- **3.91.x–3.93.0 KNOWN ISSUE:** PyPI proxy whose remote is *another Nexus* (chained) may 404 on relative-link wheels. Direct PyPI.org proxies unaffected — confirm before stage/prod.
- Minor bumps regularly add new repo formats + CVE fixes (3.93.0 fixed CVE-2026-45292 via opentelemetry 1.61.0).

## Upgrade log
| Date | Version | Outcome | PR |
|------|---------|---------|----|
| 2026-06-08 | 3.92.3 → 3.93.0 | clean build + applied to ci-dev; flagged auth rate-limit + PyPI chained-proxy known issue | #13077 |

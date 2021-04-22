# infra-renovate-config

Renovate configuration owned by Infra team.
This is currently not widely used but has potential to avoid duplication.

## Known Users

- https://github.com/camunda/infra-argocd
- https://github.com/camunda/infra-vault-template
- https://github.com/camunda/infra-seed-jobs

## Usage

Create a file `.github/renovate.json5`:
```json5
{
  $schema: "https://docs.renovatebot.com/renovate-schema.json",
  extends: ["github>camunda/infra-renovate-config"],
}
```

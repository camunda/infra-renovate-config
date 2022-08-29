# infra-renovate-config

Renovate configuration owned by Infra team.
This is currently not used everywhere but we intend doing so whenever we find a repository that does not use the shared config. infra-core is a special case.

## Known Users

Alphabetically ordered, [check if outdated](https://github.com/search?q=org%3Acamunda+github%3Ecamunda%2Finfra-renovate-config&type=code):

- https://github.com/camunda/github-actions-recipes
- https://github.com/camunda/infra-argocd
- https://github.com/camunda/infra-channel-slack-bot
- https://github.com/camunda/infra-ci-analytics-proxy
- https://github.com/camunda/infra-jenkins-shared-library
- https://github.com/camunda/infra-preview-environments-ingress
- https://github.com/camunda/infra-rotation-bot
- https://github.com/camunda/infra-seed-jobs
- https://github.com/camunda/infra-vault-template
- https://github.com/camunda/jenkins-global-shared-library
- https://github.com/camunda/team-infrastructure

## Usage

Create a file `.github/renovate.json5`:

```json5
{
  $schema: "https://docs.renovatebot.com/renovate-schema.json",
  extends: ["github>camunda/infra-renovate-config:default.json5"],
}
```

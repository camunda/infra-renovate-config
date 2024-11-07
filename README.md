# infra-renovate-config

Renovate configuration owned by Infra team.
This is currently used, see the below section. We intend to use it whenever we find a repository that does not use the shared config. infra-core is a special case.

## About Renovate

[Renovate](https://docs.renovatebot.com/) is a tool that automates dependency updates in code repositories, ensuring projects stay up-to-date with the latest versions of libraries and packages. It integrates seamlessly with GitHub, scanning project files like package manifests, Dockerfiles, and more to identify outdated dependencies. Once detected, Renovate opens pull requests with updated versions, allowing developers to review and merge these changes. It can be customized to follow specific update schedules, pin or ignore certain dependencies, and enforce semantic versioning, streamlining dependency management in GitHub repositories and reducing the risk of security vulnerabilities.

> [!NOTE]
> Renovate itself is a SaaS offering which we integrated via Github App into the Camunda organization.

## Renovate Integration
In the Infra Team context, renovate runs on schedule once per week for all [repositories using it](#known-users).
It then opens Pull Requests for all dependencies which it is able to spot an update for.

### Automerges
Our [config](/default.json5) has an `automerge` section for `patch` and `minor` where we've declared specific dependencies where experience has shown upgrades are safe to merge without human intervention. This is due to either a dependency having a reputation of respecting the [SemVer convention](https://semver.org/) or us having created a reliable CI test suite for it.

For these `automerge` dependencies renovate is going to merge it's own PRs without waiting any human approval whatsoever.

### Manual Merges
If you currently own the `Maintenance DRI` role and need to handle PR reviews of our weekly renovate update message (e.g. [this one](https://camunda.slack.com/archives/CHY2S7KDJ/p1730103656096109)), make sure of the following:
* Make sure to read the [Confluence Page](https://confluence.camunda.com/display/SRE/Infra+Maintenance+Process+and+DRI+role) about the role itself
* If you're unsure about the impact of an upgrade:
  1.  Refer to our [Upgrade Guides](https://confluence.camunda.com/display/SRE/Upgrade+Guides). If there's none:
  2. Check Slack for past conversations about the topic. If there's nothing:
  3. ask your teammates in [infra-internal](https://camunda.slack.com/archives/CHY2S7KDJ).
  4. In any case: Feel free to create missing or improve existing upgrade guides.
  5. Also consider creating smoke tests for certain more complex upgrades. If proven reliable they may contribute increasing our automerge rate in the future.

## Known Users

Alphabetically ordered, [check if outdated](https://github.com/search?q=org%3Acamunda+github%3Ecamunda%2Finfra-renovate-config&type=code):

- https://github.com/camunda/camunda-download-center
- https://github.com/camunda/cawemo-infrastructure
- https://github.com/camunda/github-actions-recipes
- https://github.com/camunda/infra-argocd
- https://github.com/camunda/infra-core
- https://github.com/camunda/infra-channel-slack-bot
- https://github.com/camunda/infra-ci-analytics-proxy
- https://github.com/camunda/infra-jenkins-shared-library
- https://github.com/camunda/infra-k8s-webhook
- https://github.com/camunda/infra-preview-environments-ingress
- https://github.com/camunda/infra-dri-bot
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

## Automerge Issues

Sometimes it's not obvious why Automerges do not happen in PRs. This guide may help you fix these problems.

### :package: Wrong package name matcher
When a renovate PR states " :vertical_traffic_light: Automerge: Disabled by config. Please merge this manually once you are satisfied.",
you might check the package name (in `packageRules.matchPackageNames`) for correctness.
The PR needs to state " :vertical_traffic_light: Automerge: Enabled."

### :hourglass_flowing_sand: Delayed Automerges
PRs don't get automerged right away, even when stating that automerge is enabled. One can simply wait for the next regular run or tirgger a run manually on developer.mend.io for the respective repository (`Actions`->`Run Renovate scan`).

### Others
* [Renovate Automerge FAQ](https://docs.renovatebot.com/key-concepts/automerge/#frequent-problems-and-how-to-resolve-them)
* [Slack Thread](https://camunda.slack.com/archives/CHY2S7KDJ/p1730987552407409)

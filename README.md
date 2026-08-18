# Jira CLI

A command-line tool for automating Jira project, issue, release, and artifact
management, built for CI/CD pipelines.

> **Scope note**: this project implements project info, issue management
> (including create/delete/assign/transition), release management,
> patch-counter release automation (next/finalize/rename-base), the full
> `devops-jrmt` release-lookup/move/rename toolset, artifact upload, and
> Teams notifications — `jira-cli project ...`, `jira-cli issue ...`,
> `jira-cli release ...`, `jira-cli artifact ...`, `jira-cli notify ...`, and
> `jira-cli config check`/`test`/`field-configurations`.

## Table of Contents

- [Requirements](#requirements)
- [Install](#install)
- [Configure](#configure)
- [Usage at a Glance](#usage-at-a-glance)
- [Patch Release Automation](#patch-release-automation)
- [CI/CD Integration](#cicd-integration)
- [Additional Release Lookup/Maintenance Commands](#additional-release-lookupmaintenance-commands)
- [Issue Creation and Deletion](#issue-creation-and-deletion)
- [Notifications](#notifications)
- [Field Configurations](#field-configurations)
- [End-to-End Example: Release → Build → Notify](#end-to-end-example-release--build--notify)
- [Project Layout](#project-layout)
- [Testing](#testing)
- [Exit Codes](#exit-codes)

## Requirements

- Python 3.11+
- A Jira Cloud site and an [API token](https://id.atlassian.com/manage-profile/security/api-tokens)

## Install

```bash
pip install -e .
```

For running the test suite:

```bash
pip install -e ".[test]"
```

## Configure

Copy `.env.example` to `.env` and fill in your Jira Cloud credentials:

```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your-api-token-here
```

The API token is never printed or logged. Verify connectivity with:

```bash
jira-cli config test
```

```text
Jira connection successful.

Jira URL : https://your-domain.atlassian.net
User     : you@example.com
Status   : Connected
```

`jira-cli config check` runs the same connectivity check and instead prints
the display name/email Jira resolves the token to.

## Usage at a Glance

Every command follows the same shape: `jira-cli <group> <action> [args] [flags]`.
Run `jira-cli --help`, or `jira-cli <group> --help`, or
`jira-cli <group> <action> --help` at any time to see the full option list
for that command.

### Project

```bash
jira-cli project list
jira-cli project get PROJ
```

### Issues

```bash
jira-cli issue get PROJ-123
jira-cli issue search --jql "project = PROJ AND status = 'In Progress'" --max-results 20
jira-cli issue comment PROJ-123 --message "Deployment completed"
jira-cli issue update PROJ-123 --summary "Updated application deployment"
jira-cli issue assign PROJ-123 --user <account-id>
jira-cli issue transition PROJ-123 --status Done
```

`issue update` requires at least one of `--summary`/`--description`; see
[Issue Creation and Deletion](#issue-creation-and-deletion) for `issue create`
and `issue delete`.

### Releases

```bash
jira-cli release list --project PROJ
jira-cli release get 10001
jira-cli release create --project PROJ --name v1.3.0 --release-date 2026-09-01
jira-cli release create --project PROJ --version v1.3.0 \
  --start-date 2026-08-20 --release-date 2026-09-01 --description "Q3 release"
jira-cli release update 10001 --release-date 2026-09-10
jira-cli release update 10001 --released
jira-cli release publish 10001
jira-cli release archive 10001
jira-cli release delete 10001
```

`--name` and `--version` are interchangeable aliases for the same option on
`release create`. `release update` requires at least one field to change.
See [Patch Release Automation](#patch-release-automation) and
[Additional Release Lookup/Maintenance Commands](#additional-release-lookupmaintenance-commands)
for the automated `next`/`finalize` workflow and the raw lookup toolset.

### Artifacts

```bash
jira-cli artifact upload PROJ-123 --file ./build/application.zip
jira-cli artifact upload PROJ-123 \
  --file ./build/application.zip --file ./build/checksum.txt \
  --build-number 1542 --commit 8f3d91a --environment UAT

# Skip the auto-generated upload comment on the issue
jira-cli artifact upload PROJ-123 --file ./build/application.zip --no-comment

jira-cli artifact metadata 10099
```

`--file` may be repeated to upload multiple attachments in one call; at least
one is required.

### Output, logging, and safety flags

Most commands accept:

| Flag | Effect |
|------|--------|
| `--output/-o table\|json\|version\|branch-name` | Render as a human-readable table (default), raw JSON, just the version string, or just the branch name (the last two are primarily meaningful for `release next`/`release current`). |
| `--quiet/-q` | Print only the resulting ID — handy for scripting. |
| `--verbose/-v` | Enable debug-level logging. |
| `--dry-run` | Preview the change without calling Jira — only on commands that modify data. |

There are two exceptions: `notify teams` only supports `--dry-run` (it never
talks to Jira, so `--output`/`--quiet`/`--verbose` don't apply), and
`release clean-name` is a pure offline string utility with none of the four
flags.

`--no-verify-ssl` (top-level flag, placed *before* the command, e.g.
`jira-cli --no-verify-ssl config test`) disables TLS certificate verification
for development-only Jira instances and prints a warning when used — never
use it against production.

## Patch Release Automation

For `MAJOR.MINOR.PATCH` release trains where only the patch segment
increments (e.g. `25.10.2` → `25.10.3`), the CLI reads the current release
straight from Jira, calculates/creates the next one, moves it into position,
and tracks deployment state on the release name — no `package.json` or build
script required.

A release is identified by the plain version stored in its `description`
(set automatically when the CLI creates it), or, if that's missing, by the
leading `MAJOR.MINOR.PATCH` token in its name — so `25.10.2`,
`25.10.2 - Release Branch`, `25.10.2 - in Deployment`, and
`25.10.2 - on DEV` are all recognized as the same version `25.10.2` as it
moves through its lifecycle.

```bash
# Show the current (highest-versioned) release for a project
jira-cli release current --project PROJ

# Calculate, create-if-missing, move after the previous release, and rename
# the previous release to "<version> - in Deployment"
jira-cli release next --project PROJ

# CI/CD-friendly: prints only the version, e.g. "25.10.3"
jira-cli release next --project PROJ --output version

# Or just the branch name, e.g. "25.10.3 - Release Branch"
jira-cli release next --project PROJ --output branch-name

# Preview without creating/moving/renaming anything in Jira
jira-cli release next --project PROJ --dry-run
```

Example: if the current release in Jira is `25.10.2`, `release next`
calculates `25.10.3`, creates it as `25.10.3 - Release Branch`, moves it to
sit after `25.10.2` in the project's release list, and renames `25.10.2` to
`25.10.2 - in Deployment`. If a release for `25.10.3` already exists (e.g. a
concurrent pipeline run created it first), the existing release is returned
instead of creating a duplicate. If no matching release exists yet at all
(first-ever run for a project), the version is bootstrapped as `YY.M.1`
from today's date (e.g. `26.8.1` in August 2026).

`--output json` returns:

```json
{
  "project": "PROJ",
  "previous_release": "25.10.2",
  "previous_release_id": "10041",
  "next_release": "25.10.3",
  "branch_name": "25.10.3 - Release Branch",
  "release_date": "2026-08-17",
  "release_id": "10042",
  "created": true,
  "existing": false,
  "moved": true,
  "renamed_previous": true
}
```

Once a release has been deployed, finalize it — this renames it from its
in-progress label to an environment label and marks it released, stripping
that environment label from any other release first so only the
newly-finalized one carries it:

```bash
jira-cli release finalize --project PROJ --to-label "on DEV" --strip-token DEV
```

At the start of a new major.minor cycle, reset a release's name back to its
plain version (clearing whatever label it picked up previously):

```bash
jira-cli release rename-base --project PROJ --version 25.10.1
```

### CI/CD Integration

The recommended pattern for every CI/CD system is the same: run
`jira-cli release next --output version`, capture stdout as `APP_VERSION`,
and stop the pipeline if the command exits non-zero.

#### Jenkins

```groovy
stage('Create Jira Release') {
    steps {
        script {
            env.APP_VERSION = sh(
                script: 'jira-cli release next --project "$JIRA_PROJECT" --output version',
                returnStdout: true
            ).trim()
        }
    }
}
```

#### GitLab CI

```yaml
create_release:
  stage: release
  script:
    - |
      export APP_VERSION=$(jira-cli release next \
        --project "$JIRA_PROJECT" \
        --output version)
      echo "APP_VERSION=$APP_VERSION" >> release.env
  artifacts:
    reports:
      dotenv: release.env
```

#### Azure DevOps

```yaml
- script: |
    APP_VERSION=$(jira-cli release next --project "$(JIRA_PROJECT)" --output version)
    echo "##vso[task.setvariable variable=APP_VERSION]$APP_VERSION"
  displayName: Create Jira Release
```

A non-zero exit code means the release could not be determined or created —
pipelines should treat this as a hard stop and not proceed to build/package
with an unknown version.

#### Bitbucket Pipelines

This matches a nightly release-train pipeline with an automated DEV
activation and a manual STG activation (the pattern documented in most
"Deployment Quick Guide" runbooks): create the release branch version at
the start, then finalize it once the new code is live.

Required repository/pipeline variables: `JIRA_URL`, `JIRA_EMAIL`,
`JIRA_API_TOKEN` (all secured — see `.env.example`), `JIRA_PROJECT`, and
`TEAMS_WEBHOOK_RELEASES`.

```yaml
definitions:
  steps:
    - step: &announce-start
        name: Announce deployment start
        script:
          - pip install jira-cli
          - export APP_VERSION=$(jira-cli release current --project "$JIRA_PROJECT" --output version)
          - jira-cli notify teams --webhook "$TEAMS_WEBHOOK_RELEASES"
              --message "The deployment of version $APP_VERSION to STG and DEV is going to start soon!"

    - step: &create-release-branch
        name: Create Jira release branch version
        script:
          - pip install jira-cli
          - export APP_VERSION=$(jira-cli release next --project "$JIRA_PROJECT" --output version)
          - echo "APP_VERSION=$APP_VERSION" >> release.env
        artifacts:
          - release.env

    # ... existing STG/DEV metadata import and code upload/activation steps ...

    - step: &finalize-and-announce
        name: Finalize Jira release and announce completion
        script:
          - pip install jira-cli
          - source release.env
          - jira-cli release finalize --project "$JIRA_PROJECT"
              --to-label "on dev" --from-label "in Deployment" --strip-token dev
          - jira-cli notify teams --webhook "$TEAMS_WEBHOOK_RELEASES"
              --message "Version $APP_VERSION was released successfully to STG and DEV."

pipelines:
  custom:
    Build & Deployment [AUTOMATIC]:
      - step: *announce-start
      - step: *create-release-branch
      # ... build, metadata upload, code deploy/activate steps ...
      - step: *finalize-and-announce

    Set Version:
      - step: *create-release-branch
```

`Set Version` is triggered manually for the first deployment of the month
(or as a fallback if the automated flow got stuck) — it's the exact same
`release next` call as the nightly pipeline, just on a different trigger.

If STG is activated separately from DEV, run the same `release finalize`
shape against STG instead, once code upload there is confirmed:

```bash
jira-cli release finalize --project "$JIRA_PROJECT" \
    --to-label "on STG" --from-label "in Deployment" --strip-token STG
jira-cli notify teams --webhook "$TEAMS_WEBHOOK_RELEASES" \
    --message "Version $APP_VERSION was released successfully to STG."
```

**Not covered yet:** a semi-automated flow that deploys an epic branch to a
sandbox instance needs a version string built from a sanitized branch name,
the current date, and a build number (e.g. for `package.json`, with semver
validation) — that builder doesn't exist in this CLI yet and would be a
separate feature.

## Additional Release Lookup/Maintenance Commands

Ported from the legacy `devops-jrmt` Node.js tool, for pipelines that still
need direct lookups/edits beyond the `next`/`finalize`/`rename-base`
lifecycle above:

```bash
# Find a release by a case-sensitive substring in its name; --release-index
# picks among matches sorted by release date, newest first (default: 0)
jira-cli release get-by-name --project PROJ --name "in Deployment" [--release-index 0]

# Newest release marked released=true
jira-cli release latest-released --project PROJ

# Raw Jira field lookup for a specific version, e.g. "releaseDate", "released"
jira-cli release get-property --project PROJ --version-id 10042 --property releaseDate

# Full release objects matching a case-insensitive substring
jira-cli release find --project PROJ --search "on DEV"

# Reposition a version after another one (used internally by `release next`)
jira-cli release move --id 10043 --after-id 10042

# Strip a token from every release name containing it
jira-cli release rename-by-token --project PROJ --search DEV [--token DEV]

# Pure string utility - no Jira call
jira-cli release clean-name --name "25.10.2 - in Deployment" --token "in Deployment"
```

`rename-by-token` and `clean-name` share the exact cleanup rules used by
`finalize`'s `--strip-token`: the token is stripped (matching `/token`,
`token/`, and the bare token, in that order), duplicate slashes collapse, a
trailing slash is removed, and — only when the name has no `/` left and
never had one — everything from the first `-` onward is truncated. If
cleaning a matched release's name produces an empty string, the command
aborts immediately; any releases already renamed earlier in the same call
stay renamed.

## Issue Creation and Deletion

```bash
jira-cli issue create --project PROJ --summary "Deploy release" \
    --issue-type Task --servicefactory Platform --author <accountId> \
    [--description "..."]

jira-cli issue delete PROJ-123
```

`issue create` tags the ticket with the Service Factory cascading field
(`customfield_10829`, specific to this Jira instance's schema) and sets the
reporter to `--author` (a Jira Cloud account ID, not an email/username).

## Notifications

```bash
jira-cli notify teams --message "Deployed 25.10.3" --webhook "$TEAMS_WEBHOOK"
```

Posts an adaptive-card text message to a Microsoft Teams incoming webhook.
This does not talk to Jira at all — it's a plain HTTP POST to whatever URL
`--webhook` points at.

## Field Configurations

```bash
jira-cli config field-configurations
```

Lists Jira field configurations (`GET /rest/api/3/fieldconfiguration`).
Requires Jira global admin permission.

## End-to-End Example: Release → Build → Notify

A typical CI/CD pipeline run strings the commands above together: create the
next release, build and tag artifacts against it, then notify the team.

```bash
# 1. Calculate/create the next patch release for this project, capture just
#    the version string for use as the build number.
APP_VERSION=$(jira-cli release next --project PROJ --output version)
echo "Building version $APP_VERSION"

# 2. Build your artifact (project-specific — not part of this CLI)
#    ... your build tool here, producing ./build/application.zip ...

# 3. Attach the build output to the ticket tracking the release
jira-cli artifact upload PROJ-123 --file ./build/application.zip \
  --build-number "$APP_VERSION" --commit "$(git rev-parse --short HEAD)" \
  --environment UAT

# 4. Move the release through its lifecycle once deployed
jira-cli release finalize --project PROJ --to-label "on UAT" --strip-token UAT

# 5. Let the team know
jira-cli notify teams --message "Deployed $APP_VERSION to UAT" --webhook "$TEAMS_WEBHOOK"
```

Because every step exits non-zero on failure (see [Exit Codes](#exit-codes)),
add `set -e` (or the CI-native equivalent) so the pipeline stops immediately
if, say, the release couldn't be created or the artifact upload failed.

## Project Layout

```text
src/jira_cli/
├── main.py           # Typer app, top-level --no-verify-ssl callback, error -> exit code mapping
├── cli/              # One module per command group (config, project, issue, release, artifact)
├── client/           # JiraClient (httpx wrapper), auth, exception hierarchy
├── services/         # Business logic, one service per resource
├── models/           # Frozen dataclasses mapping Jira API JSON <-> CLI output
├── versioning/       # MAJOR.MINOR.PATCH parsing/validation/increment (patch.py)
├── config/           # Settings loaded from environment/.env
└── utils/            # Logging (with secret masking), output rendering, CLI validators
```

## Testing

```bash
pip install -e ".[test]"
pytest
```

Tests mock `JiraClient`/`httpx` directly, so the suite runs without a live
Jira instance. Coverage includes `MAJOR.MINOR.PATCH` increment/bootstrap
calculation, duplicate-release detection, issue assign/transition, artifact
validation/upload, Teams notification, and JiraClient's
HTTP-status-to-exit-code mapping.

## Exit Codes

| Code | Meaning                                          |
|------|---------------------------------------------------|
| 0    | Success                                          |
| 1    | General error                                    |
| 2    | Invalid CLI arguments                            |
| 3    | Authentication failure                           |
| 4    | Authorization/permission failure                 |
| 5    | Resource not found                               |
| 6    | Validation failure / invalid `MAJOR.MINOR.PATCH` version / invalid release date |
| 7    | Network/API failure                              |
| 8    | File/artifact failure                            |
| 9    | Release creation failure                         |

CI/CD pipelines should treat any non-zero exit code as failure.

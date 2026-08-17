# Jira CLI

A command-line tool for automating Jira project, issue, release, and artifact
management, built for CI/CD pipelines.

> **Scope note**: this project implements project info, issue management
> (including assign/transition), release management, patch-counter release
> automation (next/finalize/rename-base), and artifact upload —
> `jira-cli project ...`, `jira-cli issue ...`, `jira-cli release ...`,
> `jira-cli artifact ...`, and `jira-cli config check`/`test`.

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

## Usage

```bash
jira-cli config check
jira-cli config test

jira-cli project list
jira-cli project get PROJ

jira-cli issue get PROJ-123
jira-cli issue search --jql "project = PROJ AND status = 'In Progress'"
jira-cli issue comment PROJ-123 --message "Deployment completed"
jira-cli issue update PROJ-123 --summary "Updated application deployment"
jira-cli issue assign PROJ-123 --user <account-id>
jira-cli issue transition PROJ-123 --status Done

jira-cli release list --project PROJ
jira-cli release get 10001
jira-cli release create --project PROJ --name v1.3.0 --release-date 2026-09-01
jira-cli release update 10001 --release-date 2026-09-10
jira-cli release publish 10001
jira-cli release archive 10001
jira-cli release delete 10001

jira-cli artifact upload PROJ-123 --file ./build/application.zip
jira-cli artifact upload PROJ-123 \
  --file ./build/application.zip --file ./build/checksum.txt \
  --build-number 1542 --commit 8f3d91a --environment UAT
jira-cli artifact metadata 10099
```

All commands support `--output table|json`, `--quiet`, and `--verbose`.
Commands that modify data also support `--dry-run`.

`--no-verify-ssl` (top-level flag, before the command) disables TLS
certificate verification for development-only Jira instances and prints a
warning when used — never use it against production.

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
(first-ever run for a project), the version is bootstrapped as `YY.MM.1`
from today's date.

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

## Project Layout

```text
src/jira_cli/
├── main.py           # Typer app, top-level --no-verify-ssl callback, error -> exit code mapping
├── cli/              # One module per command group (config, project, issue, release, artifact)
├── client/           # JiraClient (httpx wrapper), auth, exception hierarchy
├── services/         # Business logic, one service per resource
├── models/           # Frozen dataclasses mapping Jira API JSON <-> CLI output
├── versioning/       # CalVer (YY.MM.DD) parsing/validation/calculation
├── config/           # Settings loaded from environment/.env
└── utils/            # Logging (with secret masking), output rendering, CLI validators
```

## Testing

```bash
pip install -e ".[test]"
pytest
```

Tests mock `JiraClient`/`httpx` directly, so the suite runs without a live
Jira instance. Coverage includes CalVer calculation (including leap years and
year rollover), the `--date` override rules, duplicate-release detection,
issue assign/transition, artifact validation/upload, and JiraClient's
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
| 6    | Validation failure / invalid CalVer version / invalid release date |
| 7    | Network/API failure                              |
| 8    | File/artifact failure                            |
| 9    | Release creation failure                         |

CI/CD pipelines should treat any non-zero exit code as failure.

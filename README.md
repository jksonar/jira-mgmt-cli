# Jira CLI

A command-line tool for automating Jira project, issue, release, and artifact
management, built for CI/CD pipelines.

> **Scope note**: this project implements project info, issue management
> (including assign/transition), release management, CalVer release
> automation with optional custom release dates, and artifact upload —
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

## CalVer Release Automation

For monthly `YY.MM.DD` (CalVer) release trains — where the day is always the
last day of the month — the CLI can read the current release and calculate/
create the next one automatically, without a human doing the date math:

```bash
# Show the current (latest valid CalVer) release for a project
jira-cli release current --project PROJ

# Calculate, create-if-missing, and return the next monthly release
jira-cli release next --project PROJ

# CI/CD-friendly: prints only the version, e.g. "26.08.31"
jira-cli release next --project PROJ --output version

# Preview without creating anything in Jira
jira-cli release next --project PROJ --dry-run

# Override the automatic date with an explicit one (never pushed to month-end)
jira-cli release next --project PROJ --date 2026-08-20 --output version
```

Example: if the latest valid release in Jira is `26.07.31`, `release next`
calculates `26.08.31` (the last day of the following month), creates it if it
doesn't already exist, and returns it. If it already exists (e.g. a
concurrent pipeline run created it first), the existing release is returned
instead of creating a duplicate.

If `--date YYYY-MM-DD` is supplied, it always takes priority: the CLI
converts it directly to `YY.MM.DD` and never replaces it with the last day of
the month. An invalid `--date` produces `ERROR: Invalid release date.` with
exit code 6.

`--output json` returns:

```json
{
  "project": "PROJ",
  "previous_release": "26.07.31",
  "next_release": "26.08.31",
  "release_date": "2026-08-31",
  "release_id": "10042",
  "created": true,
  "existing": false
}
```

### CI/CD example (Jenkins)

```groovy
script {
    env.APP_VERSION = sh(
        script: 'jira-cli release next --project "$JIRA_PROJECT" --output version',
        returnStdout: true
    ).trim()
}
```

The same pattern (capture stdout from `--output version`) works for GitLab CI
and Azure DevOps pipelines.

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

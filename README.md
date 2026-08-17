# Jira CLI

A command-line tool for automating Jira project, issue, and release management, built for CI/CD pipelines.

> **Scope note**: this project currently implements project info, issue
> management, and release management (`jira-cli project ...`,
> `jira-cli issue ...`, `jira-cli release ...`, and `jira-cli config check`).
> Artifact commands from the full PRD are planned for a later milestone.

## Install

```bash
pip install -e .
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

jira-cli project list
jira-cli project get PROJ

jira-cli issue get PROJ-123
jira-cli issue search --jql "project = PROJ AND status = 'In Progress'"
jira-cli issue comment PROJ-123 --message "Deployment completed"
jira-cli issue update PROJ-123 --summary "Updated application deployment"

jira-cli release list --project PROJ
jira-cli release get 10001
jira-cli release create --project PROJ --name v1.3.0 --release-date 2026-09-01
jira-cli release update 10001 --release-date 2026-09-10
jira-cli release publish 10001
jira-cli release archive 10001
jira-cli release delete 10001
```

All commands support `--output table|json`, `--quiet`, and `--verbose`.
Commands that modify data also support `--dry-run`.

## Exit Codes

| Code | Meaning               |
|------|-----------------------|
| 0    | Success               |
| 1    | General error         |
| 2    | Invalid CLI arguments |
| 3    | Authentication failure|
| 4    | Authorization failure |
| 5    | Resource not found    |
| 6    | Validation failure    |
| 7    | Network/API failure   |
| 8    | File/artifact failure (reserved) |

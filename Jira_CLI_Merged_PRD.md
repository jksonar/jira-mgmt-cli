# Product Requirements Document (PRD)

# Jira CLI — Jira & CI/CD Automation Tool

## 1. Product Overview

### Product Name

**Jira CLI**

### Product Type

Python-based Command Line Interface (CLI) for automating Jira project, issue, release/version, and artifact operations through the Jira REST API.

### Objective

Jira CLI will provide developers, DevOps engineers, release managers, and CI/CD pipelines with a simple, secure, scriptable interface to Jira without requiring manual Jira UI operations.

The initial product focuses on:

1. Jira authentication and configuration
2. Jira project operations
3. Jira issue operations
4. Jira release/version management
5. Automated monthly release version generation
6. Optional custom release dates
7. Artifact upload to Jira issues
8. CI/CD integration
9. Machine-readable output and predictable exit codes

The long-term goal is to evolve the tool into a **Jira DevOps CLI** connecting Jira release management with build and deployment workflows.

---

# 2. Problem Statement

Development and DevOps teams frequently perform Jira operations during development and deployment workflows.

Typical activities include:

- Creating Jira releases/versions
- Updating release dates
- Publishing releases
- Attaching build artifacts to bitbucket repository download artifacts like https://developer.atlassian.com/cloud/bitbucket/rest/api-group-downloads/#api-repositories-workspace-repo-slug-downloads-get
- Adding deployment comments
- Updating issue status
- Searching Jira issues
- Running Jira operations from Jenkins, GitLab CI, Azure DevOps, or local terminals

Performing these activities manually is repetitive and makes CI/CD automation harder.

The Jira CLI will standardize these operations through a single Python CLI.

---

# 3. Goals

## Primary Goals

- Provide a simple Python CLI for Jira automation.
- Support Jira Cloud REST APIs.
- Support Jira Server/Data Center where practical.
- Support API-token authentication.
- Support environment-variable based configuration.
- Provide optional configuration files.
- Provide human-readable output.
- Provide JSON output for automation.
- Provide version-only output for CI/CD.
- Provide meaningful exit codes.
- Provide secure credential handling.
- Support dry-run mode.
- Support release automation.
- Support artifact upload.
- Make the application modular and testable.

## Release Automation Goals

The release automation feature must:

- Read the current Jira release.
- Identify the latest valid CalVer release.
- Automatically calculate the next monthly release.
- Use the last day of the next month by default.
- Allow the user to provide a custom release date.
- Never modify an explicitly supplied date.
- Validate release dates.
- Prevent duplicate releases.
- Return the Jira release ID.
- Return the generated version.
- Work reliably from CI/CD pipelines.

---

# 4. Non-Goals

The initial version will not:

- Replace the Jira web interface.
- Implement a complete Jira UI.
- Manage every Jira API endpoint.
- Store Jira passwords.
- Automatically modify Jira data without an explicit CLI command.
- Implement complete Jira workflow configuration management.
- Implement Jira plugin development.
- Automatically deploy applications in the MVP.
- Replace Jenkins, GitLab CI, or Azure DevOps.

---

# 5. Target Users

## Developer

Uses the CLI to perform Jira operations locally.

Example:

```bash
jira-cli issue comment PROJ-123 \
  --message "Build completed successfully"
```

## DevOps Engineer

Uses the CLI from CI/CD pipelines.

Example:

```bash
jira-cli release next \
  --project PROJ \
  --output version
```

## Release Manager

Uses the CLI to create and manage Jira releases.

Example:

```bash
jira-cli release list --project PROJ
```

## CI/CD Pipeline

Jenkins, GitLab CI, Azure DevOps, or another automation system can execute commands such as:

```bash
jira-cli release next \
  --project PROJ \
  --output version
```

and:

```bash
jira-cli artifact upload PROJ-123 \
  --file build/application.zip
```

---

# 6. High-Level Architecture

```text
                         User / CI/CD
                              |
                              v
                    +----------------------+
                    |       Jira CLI        |
                    |       Python App      |
                    +----------+-----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
        CLI Commands     Configuration      Logging
              |
              v
        Command Services
              |
       +------+------+------+------+
       |      |      |      |      |
       v      v      v      v      v
    Project Issue Release Artifact Config
              |
              v
        Jira API Client
              |
              v
        Jira REST API
              |
              v
       Jira Cloud / DC
```

For CI/CD release automation:

```text
CI/CD Pipeline
      |
      v
jira-cli release next
      |
      +--> Read current Jira release
      |
      +--> Determine release date
      |       |
      |       +--> --date provided -> validate/use supplied date
      |       |
      |       +--> no --date -> calculate last day of next month
      |
      +--> Generate YY.MM.DD version
      |
      +--> Check duplicate
      |
      +--> Create/use Jira release
      |
      v
APP_VERSION
      |
      v
Build
      |
      v
Package
      |
      v
Deploy
```

---

# 7. Technology Stack

## Programming Language

Python 3.11+

## CLI Framework

**Typer**

Alternatives:

- Click
- argparse

Typer is preferred for clean command definitions and automatic help generation.

## HTTP Client

**httpx**

## Configuration

- Environment variables
- `.env`
- Optional YAML/TOML configuration

## Authentication

Initial:

- Jira email
- Jira API token

Future:

- OAuth 2.0
- Personal access tokens where supported
- AWS Secrets Manager
- HashiCorp Vault

## Testing

- pytest
- pytest-mock
- HTTP mocking

## Quality and Security

- ruff
- mypy
- bandit

## Packaging

Use:

```text
pyproject.toml
```

Build with:

```bash
python -m build
```

---

# 8. Project Structure

```text
jira-cli/
│
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .gitignore
├── .env.example
│
├── src/
│   └── jira_cli/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── project.py
│       │   ├── issue.py
│       │   ├── release.py
│       │   └── artifact.py
│       │
│       ├── client/
│       │   ├── __init__.py
│       │   ├── jira_client.py
│       │   ├── authentication.py
│       │   └── exceptions.py
│       │
│       ├── services/
│       │   ├── project_service.py
│       │   ├── issue_service.py
│       │   ├── release_service.py
│       │   └── artifact_service.py
│       │
│       ├── models/
│       │   ├── project.py
│       │   ├── issue.py
│       │   ├── release.py
│       │   └── artifact.py
│       │
│       ├── versioning/
│       │   ├── __init__.py
│       │   └── calver.py
│       │
│       ├── config/
│       │   └── settings.py
│       │
│       └── utils/
│           ├── logger.py
│           ├── output.py
│           └── validators.py
│
└── tests/
    ├── test_project.py
    ├── test_issue.py
    ├── test_release.py
    ├── test_calver.py
    ├── test_artifact.py
    └── test_jira_client.py
```

---

# 9. CLI Command Design

General syntax:

```text
jira-cli <resource> <action> [options]
```

Initial command groups:

```text
jira-cli
│
├── config
│   └── test
│
├── project
│   ├── list
│   └── get
│
├── issue
│   ├── get
│   ├── search
│   ├── update
│   ├── comment
│   ├── assign
│   └── transition
│
├── release
│   ├── current
│   ├── list
│   ├── get
│   ├── next
│   ├── create
│   ├── update
│   ├── publish
│   ├── archive
│   └── delete
│
└── artifact
    ├── upload
    └── metadata
```

---

# 10. Authentication

Environment variables:

```bash
export JIRA_URL="https://company.atlassian.net"
export JIRA_EMAIL="devops@example.com"
export JIRA_API_TOKEN="xxxxxxxx"
```

Connection test:

```bash
jira-cli config test
```

Expected output:

```text
Jira connection successful.

Jira URL : https://company.atlassian.net
User     : devops@example.com
Status   : Connected
```

The API token must never be printed in logs.

---

# 11. Configuration File

Optional configuration:

```yaml
jira:
  url: https://company.atlassian.net
  email: devops@example.com

defaults:
  project: PROJ

output:
  format: table
```

Credentials should preferably remain outside the configuration file.

Example:

```bash
JIRA_API_TOKEN=xxxxxxxx
```

---

# 12. Project Commands

## List Projects

```bash
jira-cli project list
```

## Get Project

```bash
jira-cli project get PROJ
```

Example:

```text
Project Key: PROJ
Name: Product Development
Lead: John Doe
Type: software
```

---

# 13. Release Management

Jira releases are represented as project versions.

The CLI will support both traditional release commands and automated monthly release generation.

## List Releases

```bash
jira-cli release list --project PROJ
```

## Get Release

```bash
jira-cli release get 10001
```

## Create Release

```bash
jira-cli release create \
  --project PROJ \
  --name v1.3.0 \
  --release-date 2026-09-01
```

Optional:

```text
--description
--start-date
--release-date
--released
```

## Update Release

```bash
jira-cli release update 10001 \
  --name v1.3.1 \
  --release-date 2026-09-10
```

## Publish Release

```bash
jira-cli release publish 10001
```

## Archive Release

```bash
jira-cli release archive 10001
```

## Delete Release

```bash
jira-cli release delete 10001
```

---

# 14. CalVer Release Versioning

The Jira CLI release automation will use **Calendar Versioning (CalVer)**.

Default format:

```text
YY.MM.DD
```

The default release date is the **last day of the next month**.

Examples:

```text
26.07.31
26.08.31
26.09.30
26.10.31
26.11.30
26.12.31
27.01.31
```

This is a monthly release convention, rather than Semantic Versioning.

---

# 15. Automatic Next Release

Primary command:

```bash
jira-cli release next --project PROJ
```

The CLI will:

1. Connect to Jira.
2. Retrieve project releases.
3. Identify the latest valid CalVer release.
4. Determine whether `--date` was supplied.
5. If no date is supplied, calculate the next month.
6. Calculate the last day of that month.
7. Generate the `YY.MM.DD` version.
8. Check whether the version already exists.
9. Create the release if it does not exist.
10. Return the version and Jira release ID.

Example:

```text
Current Release : 26.07.31
Next Release    : 26.08.31
Status          : CREATED
```

---

# 16. Custom Release Date

The user can override the automatic release date.

Command:

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-08-20
```

The resulting Jira version is:

```text
26.08.20
```

Input date format:

```text
YYYY-MM-DD
```

Jira version format:

```text
YY.MM.DD
```

Example:

```text
CLI Date       Jira Version
--------------------------------
2026-08-20  ->  26.08.20
2026-08-25  ->  26.08.25
2026-08-31  ->  26.08.31
2026-09-15  ->  26.09.15
2027-01-31  ->  27.01.31
```

---

# 17. Date Selection Rules

The CLI must follow this priority:

```text
                 --date provided?
                        |
             +----------+----------+
             |                     |
            YES                    NO
             |                     |
             v                     v
      Validate supplied      Read current release
           date                    |
             |                     v
             v               Calculate next month
       YY.MM.DD version            |
             |                     v
             |                Last day of month
             |                     |
             +----------+----------+
                        |
                        v
                 Check Jira Release
                        |
                        v
                Create if required
```

### Rule 1 — No Date

```bash
jira-cli release next --project PROJ
```

Automatically calculate:

```text
YY.MM.LAST_DAY_OF_MONTH
```

### Rule 2 — Date Provided

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-08-25
```

Use:

```text
26.08.25
```

### Rule 3 — Explicit Date Has Priority

If `--date` is provided, the CLI must not replace it with the last day of the month.

For example:

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-08-15
```

must produce:

```text
26.08.15
```

and not:

```text
26.08.31
```

---

# 18. Date Validation

The CLI must validate user-provided dates.

Valid:

```text
2026-08-20
2026-08-31
2026-09-30
2027-02-28
2028-02-29
```

Invalid:

```text
2026-08-32
2026-02-30
2026-13-01
2026-00-10
abc
```

Invalid input must produce:

```text
ERROR: Invalid release date.

Expected format:
YYYY-MM-DD

Example:
2026-08-20
```

---

# 19. Release Version Validation

The CLI must validate Jira versions before using them for automated release calculation.

Expected format:

```text
YY.MM.DD
```

Valid:

```text
26.08.31
26.09.30
27.01.31
```

Invalid:

```text
1.2.3
26.8.31
2026.08.31
26-08-31
```

The CLI should ignore unrelated Jira versions such as:

```text
v1.0.0
release-test
legacy-release
```

when identifying the latest CalVer release.

---

# 20. Current Release Command

```bash
jira-cli release current --project PROJ
```

Example:

```text
Current Jira Release

Project : PROJ
Version : 26.07.31
Release : Unreleased
```

JSON:

```bash
jira-cli release current \
  --project PROJ \
  --output json
```

```json
{
  "project": "PROJ",
  "version": "26.07.31",
  "released": false
}
```

---

# 21. Release Calculation Examples

```text
26.07.31 -> 26.08.31
26.08.31 -> 26.09.30
26.09.30 -> 26.10.31
26.11.30 -> 26.12.31
26.12.31 -> 27.01.31
28.01.31 -> 28.02.29
27.01.31 -> 27.02.28
```

The implementation must use a real calendar calculation rather than hard-coded month lengths.

---

# 22. Future-Date Support

The CLI may allow a user to specify a future date:

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-10-15
```

Result:

```text
Current Release : 26.07.31
Requested Date  : 2026-10-15
Next Release    : 26.10.15
Status          : CREATED
```

Unless a future business rule restricts releases to the immediate next month, an explicit date should be accepted.

---

# 23. Duplicate Release Handling

Before creating a release, the CLI must check whether the target version already exists.

If `26.08.20` already exists, the CLI must not create a duplicate.

Example:

```text
Release 26.08.20 already exists.

Release ID: 10042
```

The command should still return the existing version and release ID so that CI/CD can continue safely.

JSON:

```json
{
  "project": "PROJ",
  "previous_release": "26.07.31",
  "next_release": "26.08.20",
  "release_date": "2026-08-20",
  "release_id": "10042",
  "created": false,
  "existing": true
}
```

---

# 24. No Existing CalVer Release

If Jira contains no valid CalVer release:

```text
ERROR: No valid CalVer release found.

Expected format:
YY.MM.DD

Example:
26.08.31
```

The MVP should not silently guess an initial release.

A future initialization command may be added:

```bash
jira-cli release init \
  --project PROJ \
  --version 26.08.31
```

---

# 25. Version-Only Output

For CI/CD, the recommended command is:

```bash
jira-cli release next \
  --project PROJ \
  --output version
```

Output:

```text
26.08.31
```

With a custom date:

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-08-20 \
  --output version
```

Output:

```text
26.08.20
```

No additional output should be printed in `version` mode.

---

# 26. JSON Output

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-08-20 \
  --output json
```

Example:

```json
{
  "project": "PROJ",
  "previous_release": "26.07.31",
  "next_release": "26.08.20",
  "release_date": "2026-08-20",
  "release_id": "10042",
  "created": true
}
```

Automatic date:

```json
{
  "project": "PROJ",
  "previous_release": "26.07.31",
  "next_release": "26.08.31",
  "release_date": "2026-08-31",
  "release_id": "10042",
  "created": true
}
```

---

# 27. Output Formats

The CLI should support:

- Table — default human-readable format
- JSON — machine-readable format
- Version — CI/CD-friendly version-only output
- Quiet — essential identifier only where appropriate

---

# 28. Dry Run

All modifying operations should support:

```bash
--dry-run
```

Example:

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-08-20 \
  --dry-run
```

Output:

```text
DRY RUN

Current Release : 26.07.31
Release Date    : 2026-08-20
Next Release    : 26.08.20

No changes will be made to Jira.
```

---

# 29. Issue Management

## Get Issue

```bash
jira-cli issue get PROJ-123
```

## Search Issues

```bash
jira-cli issue search \
  --jql "project = PROJ AND status = 'In Progress'"
```

## Add Comment

```bash
jira-cli issue comment PROJ-123 \
  --message "Deployment completed successfully."
```

## Assign Issue

```bash
jira-cli issue assign PROJ-123 \
  --user john.doe
```

## Transition Issue

```bash
jira-cli issue transition PROJ-123 \
  --status Done
```

## Update Issue

```bash
jira-cli issue update PROJ-123 \
  --summary "Updated application deployment"
```

---

# 30. Artifact Upload

A major feature is uploading build artifacts to Jira issues.

Basic command:

```bash
jira-cli artifact upload PROJ-123 \
  --file ./build/application.zip
```

Multiple files:

```bash
jira-cli artifact upload PROJ-123 \
  --file ./build/application.zip \
  --file ./build/checksum.txt
```

The CLI must validate that the file:

- Exists
- Is readable
- Is a regular file
- Is within configured size limits where known

Optional metadata:

```bash
jira-cli artifact upload PROJ-123 \
  --file application-26.08.20.zip \
  --build-number 1542 \
  --environment UAT \
  --commit 8f3d91a
```

Possible Jira comment:

```text
Artifact uploaded successfully.

Name: application-26.08.20.zip
Build: 1542
Commit: 8f3d91a
Environment: UAT
```

---

# 31. Artifactory Integration

If the term artifact refers to **JFrog Artifactory**, a future integration may support:

```text
CI/CD
 |
 +--> Jira CLI
 |      |
 |      +--> Create Jira Release
 |
 +--> Artifactory
        |
        +--> Upload Artifact
```

The Jira issue/release can then contain the Artifactory artifact URL.

This is outside the initial MVP unless explicitly enabled as part of the project scope.

---

# 32. CI/CD Integration

The Jira CLI is designed to be executed from CI/CD systems.

Recommended workflow:

```text
CI/CD Pipeline
      |
      v
jira-cli release next
      |
      +--> Read current release
      |
      +--> Determine date
      |
      +--> Calculate version
      |
      +--> Check Jira
      |
      +--> Create/use release
      |
      v
APP_VERSION
      |
      v
Build
      |
      v
Package
      |
      v
Deploy
```

---

# 33. Jenkins Integration

## Automatic Date

```groovy
stage('Create Jira Release') {
    steps {
        script {
            env.APP_VERSION = sh(
                script: '''
                    jira-cli release next \
                        --project "$JIRA_PROJECT" \
                        --output version
                ''',
                returnStdout: true
            ).trim()

            echo "Application Version: ${env.APP_VERSION}"
        }
    }
}
```

## Custom Date

```groovy
parameters {
    string(
        name: 'RELEASE_DATE',
        defaultValue: '',
        description: 'Optional release date in YYYY-MM-DD format'
    )
}
```

Then the pipeline can pass `--date` only when the parameter is populated.

Example:

```text
RELEASE_DATE=2026-08-20
APP_VERSION=26.08.20
```

---

# 34. GitLab CI Integration

Automatic:

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

Custom date:

```yaml
create_release:
  stage: release
  script:
    - |
      export APP_VERSION=$(jira-cli release next \
        --project "$JIRA_PROJECT" \
        --date "$RELEASE_DATE" \
        --output version)

      echo "APP_VERSION=$APP_VERSION" >> release.env
  artifacts:
    reports:
      dotenv: release.env
```

---

# 35. Azure DevOps Integration

```yaml
steps:

- script: |
    APP_VERSION=$(jira-cli release next \
      --project "$(JIRA_PROJECT)" \
      --output version)

    echo "##vso[task.setvariable variable=APP_VERSION]$APP_VERSION"

  displayName: Create Jira Release

- script: |
    echo "Building version $(APP_VERSION)"
  displayName: Build

- script: |
    echo "Deploying version $(APP_VERSION)"
  displayName: Deploy
```

---

# 36. CI/CD Failure Behavior

The CLI must fail safely.

Example:

```text
ERROR: Unable to connect to Jira.
```

A non-zero exit code must be returned.

Expected behavior:

```text
Jira Release Creation
        |
        +---- SUCCESS ----> Build
        |
        +---- FAILURE ----> STOP
```

CI/CD must not continue with an unknown release version.

---

# 37. Exit Codes

Recommended exit codes:

```text
0   Success
1   General error
2   Invalid CLI arguments
3   Authentication failure
4   Authorization failure
5   Jira resource not found
6   Validation failure
7   Network/API failure
8   File/artifact failure
9   Release creation failure
```

---

# 38. Error Handling

Authentication:

```text
ERROR: Jira authentication failed.

HTTP Status: 401

Please verify:
- JIRA_URL
- JIRA_EMAIL
- JIRA_API_TOKEN
```

Permission:

```text
ERROR: Permission denied.

You do not have permission to create releases
for project PROJ.
```

Issue not found:

```text
ERROR: Jira issue PROJ-999 was not found.
```

File error:

```text
ERROR: Artifact file does not exist:

./build/application.zip
```

---

# 39. Logging

Logging levels:

```text
ERROR
WARNING
INFO
DEBUG
```

Verbose mode:

```bash
jira-cli release next \
  --project PROJ \
  --verbose
```

Example:

```text
DEBUG: Jira URL: https://company.atlassian.net
DEBUG: Request: GET /rest/api/3/project/PROJ/versions
DEBUG: Current release: 26.07.31
DEBUG: Calculated release: 26.08.31
DEBUG: Request: POST /rest/api/3/version
DEBUG: Response: 201
```

Secrets must never appear in logs.

---

# 40. Security Requirements

## Credential Protection

Do not encourage passing tokens directly on the command line.

Preferred:

```bash
JIRA_API_TOKEN=xxxxx
```

or a secure credential store.

## Token Masking

Logs must mask credentials:

```text
JIRA_API_TOKEN=********
```

## TLS

HTTPS must be used for production Jira instances.

Certificate verification must be enabled by default.

An insecure development-only option may be provided:

```bash
--no-verify-ssl
```

If used, the CLI must display a warning.

---

# 41. Jira API Client Design

The Jira API client must abstract HTTP communication.

Conceptual interface:

```python
class JiraClient:

    def get(self, endpoint, params=None):
        pass

    def post(self, endpoint, json=None, files=None):
        pass

    def put(self, endpoint, json=None):
        pass

    def delete(self, endpoint):
        pass
```

Services should use `JiraClient` instead of calling `httpx` directly.

Architecture:

```text
CLI
 |
 v
ReleaseService
 |
 v
JiraClient
 |
 v
Jira REST API
```

---

# 42. API Version Strategy

Jira API endpoint paths must be isolated inside the client/service layer.

For Jira Cloud, the initial implementation should target REST API v3 where supported.

Do not spread endpoint strings throughout the application.

Use centralized configuration such as:

```python
JIRA_API_VERSION = "3"
```

---

# 43. Service Layer

## ReleaseService

Responsibilities:

```text
list_releases()
get_release()
get_current_release()
calculate_next_release()
validate_release_date()
create_release()
update_release()
publish_release()
archive_release()
delete_release()
```

## IssueService

Responsibilities:

```text
get_issue()
search_issues()
update_issue()
add_comment()
assign_issue()
transition_issue()
```

## ArtifactService

Responsibilities:

```text
upload_artifact()
upload_multiple_artifacts()
validate_artifact()
get_attachment_metadata()
```

## VersionService

Responsibilities:

```text
parse_version()
validate_version()
calculate_next_month()
calculate_last_day_of_month()
date_to_version()
version_to_date()
```

---

# 44. Testing Strategy

## Unit Tests

Test:

- Authentication
- Request construction
- Release creation
- Release update
- Release calculation
- Date validation
- CalVer parsing
- CalVer generation
- Duplicate detection
- Issue search
- Issue comments
- Artifact validation
- Artifact upload
- Error handling

## Required CalVer Tests

```text
26.07.31 -> 26.08.31
26.08.31 -> 26.09.30
26.09.30 -> 26.10.31
26.11.30 -> 26.12.31
26.12.31 -> 27.01.31
28.01.31 -> 28.02.29
27.01.31 -> 27.02.28
```

## Custom Date Tests

```text
2026-08-20 -> 26.08.20
2026-08-25 -> 26.08.25
2026-09-15 -> 26.09.15
```

Invalid:

```text
2026-08-32
2026-02-30
2026-13-01
abc
```

## Integration Tests

Integration tests should run against a dedicated Jira test project.

```text
Jira Test Instance
       |
       v
Test Project
       |
       +--> Test Release
       +--> Test Issue
       +--> Test Attachment
```

Most unit tests should mock Jira API responses to avoid unnecessary dependence on a live Jira environment.

---

# 45. Project CI/CD

The Jira CLI project itself should use CI/CD.

Pipeline:

```text
Lint
  |
  v
Unit Test
  |
  v
Build
  |
  v
Security Scan
  |
  v
Package
  |
  v
Publish
```

Recommended tools:

```text
ruff
pytest
mypy
bandit
build
twine
```

---

# 46. Packaging

The CLI should be installable as a Python package.

Example:

```bash
pip install jira-cli
```

Then:

```bash
jira-cli --help
```

The package must expose the console entry point:

```text
jira-cli
```

---

# 47. pyproject.toml

Example:

```toml
[project]
name = "jira-cli"
version = "0.1.0"
description = "A Python CLI for Jira automation"
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    "typer",
    "httpx",
    "python-dotenv",
    "rich",
]

[project.scripts]
jira-cli = "jira_cli.main:app"

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

The exact dependency versions should be pinned or constrained as part of implementation.

---

# 48. Help System

Running:

```bash
jira-cli --help
```

should display:

```text
Usage: jira-cli [OPTIONS] COMMAND [ARGS]...

Jira automation CLI.

Commands:
  config      Manage configuration
  project     Project operations
  issue       Issue operations
  release     Release operations
  artifact    Artifact operations

Options:
  --verbose
  --output
  --dry-run
  --help
```

Command-specific help:

```bash
jira-cli release next --help
```

must clearly document:

```text
--project
--date
--output
--dry-run
--verbose
```

---

# 49. MVP Scope

The MVP should focus on the core Jira automation workflow.

## Authentication

- [ ] Jira URL configuration
- [ ] Jira email configuration
- [ ] Jira API token
- [ ] Authentication validation

## Project

- [ ] List projects
- [ ] Get project

## Issue

- [ ] Get issue
- [ ] Search using JQL
- [ ] Add comment
- [ ] Update issue

## Release

- [ ] List releases
- [ ] Get release
- [ ] Read current CalVer release
- [ ] Calculate next monthly release
- [ ] Optional custom release date
- [ ] Validate custom date
- [ ] Convert date to `YY.MM.DD`
- [ ] Check duplicate release
- [ ] Create release
- [ ] Update release
- [ ] Publish release

## Artifact

- [ ] Validate file
- [ ] Upload single artifact
- [ ] Upload multiple artifacts
- [ ] Display attachment information

## CLI

- [ ] Table output
- [ ] JSON output
- [ ] Version-only output
- [ ] Quiet mode
- [ ] Verbose mode
- [ ] Dry-run mode
- [ ] Exit codes
- [ ] Error handling

## CI/CD

- [ ] Jenkins example
- [ ] GitLab CI example
- [ ] Azure DevOps example
- [ ] Environment variable support

---

# 50. Recommended Initial Milestones

## Milestone 1 — Project Foundation

- [ ] Create Python project
- [ ] Configure `pyproject.toml`
- [ ] Add Typer
- [ ] Add httpx
- [ ] Implement configuration
- [ ] Implement logging
- [ ] Implement Jira client
- [ ] Implement authentication check

## Milestone 2 — Jira Project & Issue

- [ ] Project list
- [ ] Project details
- [ ] Issue get
- [ ] Issue search
- [ ] Issue comment
- [ ] Issue update

## Milestone 3 — Release Management

- [ ] Release list
- [ ] Release get
- [ ] CalVer parser
- [ ] CalVer validator
- [ ] Automatic next release calculation
- [ ] Custom date support
- [ ] Duplicate detection
- [ ] Release create
- [ ] Release update
- [ ] Release publish
- [ ] Release archive

## Milestone 4 — Artifact Management

- [ ] File validation
- [ ] Single artifact upload
- [ ] Multiple artifact upload
- [ ] Upload result
- [ ] Attachment metadata

## Milestone 5 — CI/CD

- [ ] JSON output
- [ ] Version-only output
- [ ] Quiet mode
- [ ] Exit codes
- [ ] Jenkins example
- [ ] GitLab CI example
- [ ] Azure DevOps example
- [ ] Docker image

## Milestone 6 — Production Hardening

- [ ] Unit tests
- [ ] Integration tests
- [ ] Security scanning
- [ ] Retry mechanism
- [ ] Rate-limit handling
- [ ] Documentation
- [ ] Python package release

---

# 51. Phase 2

After the MVP:

- [ ] OAuth 2.0
- [ ] Configuration profiles
- [ ] YAML/TOML configuration improvements
- [ ] Jira workflow automation
- [ ] Bulk issue operations
- [ ] Automatic release notes
- [ ] Git commit integration
- [ ] Git tag integration
- [ ] Jenkins integration helpers
- [ ] GitLab integration helpers
- [ ] JFrog Artifactory integration
- [ ] Deployment tracking
- [ ] AWS Secrets Manager
- [ ] HashiCorp Vault
- [ ] Multiple Jira profiles

---

# 52. Phase 3 — Advanced DevOps Features

```text
Git
 |
 v
Jira CLI
 |
 +--> Create Jira Release
 |
 +--> Find Jira Issues
 |
 +--> Generate Release Notes
 |
 +--> Upload Build Artifact
 |
 +--> Add Deployment Comment
 |
 +--> Transition Jira Issues
 |
 v
Production Deployment
```

Potential command:

```bash
jira-cli deploy \
  --project PROJ \
  --version 26.08.20 \
  --issue PROJ-123 \
  --artifact ./build/application.zip \
  --environment production
```

It could:

1. Validate Jira connection.
2. Find/create release.
3. Upload artifact.
4. Add deployment comment.
5. Update Jira issue.
6. Transition issue if configured.
7. Return success/failure status.

---

# 53. Future Release Preparation Command

A future high-level command could be:

```bash
jira-cli release prepare \
  --project PROJ \
  --version 26.08.20 \
  --artifact ./build/application.zip
```

The CLI could:

1. Authenticate with Jira.
2. Validate project.
3. Check whether version exists.
4. Create version if missing.
5. Find related Jira issues.
6. Upload artifact.
7. Add release comment.
8. Generate release information.
9. Return release ID.

---

# 54. Example End-to-End Workflow

Normal monthly release:

```text
Current Jira Release
        |
        v
26.07.31
        |
        v
jira-cli release next
        |
        v
26.08.31
        |
        v
Create Jira Release
        |
        v
APP_VERSION=26.08.31
        |
        v
Build
        |
        v
Package
        |
        v
Upload Artifact
        |
        v
Deploy
```

Custom release:

```text
CI/CD
  |
  v
RELEASE_DATE=2026-08-20
  |
  v
jira-cli release next \
  --project PROJ \
  --date 2026-08-20 \
  --output version
  |
  v
APP_VERSION=26.08.20
  |
  v
Build
  |
  v
Package
  |
  v
Deploy
```

---

# 55. Success Criteria

The MVP is successful when a user can:

1. Configure Jira credentials.
2. Verify Jira connectivity.
3. List Jira projects.
4. Search Jira issues.
5. Create and manage Jira releases.
6. Read the current CalVer release.
7. Automatically calculate the next monthly release.
8. Provide an optional custom release date.
9. Validate the custom date.
10. Prevent duplicate releases.
11. Return the release version.
12. Return the Jira release ID.
13. Upload an artifact to a Jira issue.
14. Add a Jira comment.
15. Run the workflow from Jenkins/GitLab/Azure DevOps.
16. Receive predictable exit codes.
17. Receive JSON output.
18. Receive version-only output for CI/CD.

The critical CI/CD command must work reliably:

```bash
jira-cli release next \
  --project PROJ \
  --output version
```

If current Jira release is:

```text
26.07.31
```

the result should be:

```text
26.08.31
```

When a custom date is supplied:

```bash
jira-cli release next \
  --project PROJ \
  --date 2026-08-20 \
  --output version
```

the result must be:

```text
26.08.20
```

---

# 56. Final Product Workflow

```text
                         CI/CD Pipeline
                               |
                               v
                    jira-cli release next
                               |
                    +----------+----------+
                    |                     |
             --date provided?       No --date
                    |                     |
                   YES                    NO
                    |                     |
                    v                     v
             Validate date        Read current release
                    |                     |
                    v                     v
             Convert to          Calculate next month
              YY.MM.DD            Last day of month
                    |                     |
                    +----------+----------+
                               |
                               v
                         Check Jira
                               |
                     +---------+---------+
                     |                   |
                  Exists              Missing
                     |                   |
                     v                   v
               Use existing        Create release
                     |                   |
                     +---------+---------+
                               |
                               v
                         Return version
                               |
                               v
                         APP_VERSION
                               |
                               v
                             Build
                               |
                               v
                            Package
                               |
                               v
                         Artifact Upload
                               |
                               v
                            Deploy
```

---

# 57. Product Principle

> **Automate Jira operations and release creation while allowing CI/CD users to either use the standard monthly release date or explicitly choose a release date when required.**

Default:

```text
YY.MM.LAST_DAY_OF_MONTH
```

Override:

```text
--date YYYY-MM-DD
```

The Jira CLI should provide a controlled bridge between:

```text
Jira
  ↕
Jira CLI
  ↕
CI/CD
  ↕
Application Build & Deployment
```

This turns Jira CLI from a simple API wrapper into a reusable **Jira + CI/CD automation tool**.

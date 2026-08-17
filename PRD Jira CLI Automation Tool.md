# Product Requirements Document (PRD)

## 1. Product Overview

### Product Name

**Jira CLI**

### Product Type

Python-based Command Line Interface (CLI) for automating Jira project and issue management through the Jira REST API.

### Objective

The Jira CLI will provide developers, DevOps engineers, release managers, and automation pipelines with a simple command-line interface to perform common Jira operations without manually opening the Jira web interface.

The application will communicate with Jira through its REST API. Jira's REST API is designed for programmatic interaction with Jira and supports operations such as project management, issue management, attachments, and project versions.

The primary goal is to automate repetitive Jira activities such as:

- Creating releases/versions
- Updating releases
- Listing releases
- Uploading build artifacts to Jira issues
- Adding comments
- Updating issues
- Assigning issues
- Transitioning issues
- Searching issues using JQL
- Retrieving project information
- Supporting CI/CD pipelines

---

# 2. Problem Statement

Development and DevOps teams frequently need to perform Jira operations during development and deployment workflows.

Typical activities include:

1. Creating a Jira release/version.
2. Updating release dates.
3. Attaching build artifacts to Jira tickets.
4. Adding deployment information to Jira issues.
5. Updating Jira issue status.
6. Adding release comments.
7. Searching Jira issues.
8. Performing these operations from Jenkins, GitLab CI, GitHub Actions, or local terminals.

Doing these activities manually through the Jira UI is repetitive and difficult to integrate into automated CI/CD pipelines.

The Jira CLI will provide a standardized command-line interface for these operations.

---

# 3. Goals

## Primary Goals

- Provide a simple Python CLI for Jira automation.
- Support Jira Cloud REST APIs.
- Support Jira Server/Data Center where practical.
- Support API-token based authentication.
- Allow configuration through environment variables and configuration files.
- Provide human-readable CLI output.
- Provide JSON output for automation.
- Provide meaningful exit codes.
- Make the CLI suitable for CI/CD pipelines.
- Provide secure credential handling.
- Make the application modular so new Jira API operations can easily be added.

## Secondary Goals

- Support dry-run mode.
- Support verbose/debug logging.
- Support configuration profiles.
- Support artifact upload.
- Support release automation.
- Support CI/CD integration.

---

# 4. Non-Goals

The initial version will NOT attempt to:

- Replace the Jira web interface.
- Implement a complete Jira UI.
- Manage every Jira API endpoint.
- Store Jira passwords.
- Automatically modify Jira data without explicit CLI commands.
- Implement Jira workflow configuration management.
- Implement Jira plugin development.

---

# 5. Target Users

## Developer

Uses the CLI to update Jira issues during development.

Example:

```bash
jira-cli issue comment PROJ-123 \
  --message "Build completed successfully"
```

## DevOps Engineer

Uses the CLI from CI/CD pipelines.

Example:

```bash
jira-cli release create \
  --project PROJ \
  --name v2.5.0 \
  --release-date 2026-08-20
```

## Release Manager

Uses the CLI to create and manage Jira releases.

Example:

```bash
jira-cli release list --project PROJ
```

## CI/CD Pipeline

Jenkins/GitLab can execute:

```bash
jira-cli artifact upload PROJ-123 \
  --file build/app-2.5.0.zip
```

---

# 6. High-Level Architecture

```text
                    +----------------------+
                    |      User / CI/CD    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |      Jira CLI        |
                    |      Python App      |
                    +----------+-----------+
                               |
             +-----------------+----------------+
             |                 |                |
             v                 v                v
       CLI Commands       Configuration     Logging
             |
             v
       Command Services
             |
             +----------------+
             |                |
             v                v
       Jira API Client    Validators
             |
             v
       Jira REST API
             |
             v
       +-------------------+
       |      Jira         |
       | Cloud / DC        |
       +-------------------+
```

---

# 7. Proposed Technology Stack

## Programming Language

**Python 3.11+**

Python is selected because it provides:

- Excellent HTTP libraries
- Strong CLI ecosystem
- Easy CI/CD integration
- Good testing ecosystem
- Easy packaging
- Cross-platform support

## CLI Framework

Recommended:

**Typer**

Alternative:

- Click
- argparse

Typer is preferred because it provides clean command definitions and automatic help generation.

## HTTP Client

Recommended:

**httpx**

Alternative:

- requests

`httpx` should be preferred because it supports modern synchronous/asynchronous HTTP patterns.

## Configuration

Recommended:

- Environment variables
- `.env`
- YAML/TOML configuration

## Authentication

Initial implementation:

- Jira email
- Jira API token

Future:

- OAuth 2.0
- Personal access token where supported
- AWS Secrets Manager
- HashiCorp Vault

## Testing

- pytest
- pytest-mock
- HTTP mocking

## Packaging

Use:

```text
pyproject.toml
```

Build package using:

```bash
python -m build
```

---

# 8. Project Structure

Recommended project structure:

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
│       │
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── project.py
│       │   ├── issue.py
│       │   ├── release.py
│       │   ├── artifact.py
│       │   └── config.py
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
    ├── test_artifact.py
    └── test_jira_client.py
```

---

# 9. CLI Command Design

The CLI should follow this general structure:

```text
jira-cli <resource> <action> [options]
```

Examples:

```bash
jira-cli project list
jira-cli project get PROJ

jira-cli issue get PROJ-123
jira-cli issue search --jql "project = PROJ"
jira-cli issue comment PROJ-123 --message "Deployment completed"

jira-cli release list --project PROJ
jira-cli release create --project PROJ --name v1.2.0
jira-cli release update 10001 --release-date 2026-08-20
jira-cli release publish 10001

jira-cli artifact upload PROJ-123 --file ./build/app.zip
```

---

# 10. Authentication

The CLI should support environment-based authentication.

Example:

```bash
export JIRA_URL="https://company.atlassian.net"
export JIRA_EMAIL="devops@example.com"
export JIRA_API_TOKEN="xxxxxxxx"
```

Then:

```bash
jira-cli project list
```

The API token must never be printed in logs.

---

# 11. Configuration File

The CLI should optionally support:

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

Expected output:

```text
KEY       NAME                    TYPE
------------------------------------------------
PROJ      Product Development     software
DEV       Development             software
OPS       Operations              software
```

## Get Project

```bash
jira-cli project get PROJ
```

Output:

```text
Project Key: PROJ
Name: Product Development
Lead: John Doe
Type: software
```

---

# 13. Release Management

Release management is one of the primary features.

Jira represents releases as project versions. The Jira REST API provides endpoints to list, create, update, move, merge, and delete project versions. Creating a version requires appropriate Jira project administration permissions.

## List Releases

```bash
jira-cli release list --project PROJ
```

Example:

```text
VERSION     RELEASE DATE     STATUS
--------------------------------------------
v1.0.0      2026-06-01       Released
v1.1.0      2026-07-01       Released
v1.2.0      2026-08-20       Unreleased
```

## Create Release

```bash
jira-cli release create \
  --project PROJ \
  --name v1.3.0 \
  --release-date 2026-09-01
```

Optional parameters:

```bash
--description
--start-date
--release-date
--released
```

Example:

```bash
jira-cli release create \
  --project PROJ \
  --name v1.3.0 \
  --description "September production release" \
  --release-date 2026-09-01
```

## Update Release

```bash
jira-cli release update 10001 \
  --name v1.3.1 \
  --release-date 2026-09-10
```

## Release

```bash
jira-cli release publish 10001
```

The command should update the Jira version to:

```text
released = true
```

## Archive Release

```bash
jira-cli release archive 10001
```

---

# 14. Issue Management

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

# 15. Artifact Upload

A major feature of the CLI will be uploading build artifacts to Jira issues.

Jira's REST API provides:

```text
POST /rest/api/3/issue/{issueIdOrKey}/attachments
```

for adding attachments to an issue. The API requires the multipart field to be named `file` and requires the `X-Atlassian-Token: no-check` header for this operation. Jira also enforces project permissions and attachment size limits.

## Basic Command

```bash
jira-cli artifact upload PROJ-123 \
  --file ./build/application.zip
```

## Multiple Files

```bash
jira-cli artifact upload PROJ-123 \
  --file ./build/application.zip \
  --file ./build/checksum.txt
```

## Directory Upload

Future feature:

```bash
jira-cli artifact upload PROJ-123 \
  --directory ./build/
```

## Artifact Metadata

The CLI should optionally add a comment:

```text
Artifact uploaded successfully.

Name: application-1.5.0.zip
Size: 48 MB
Build: 1542
Commit: 8f3d91a
Environment: UAT
```

Example:

```bash
jira-cli artifact upload PROJ-123 \
  --file application-1.5.0.zip \
  --build-number 1542 \
  --environment UAT \
  --commit 8f3d91a
```

---

# 16. CI/CD Integration

The CLI should be designed specifically for automation.

## Jenkins Example

```groovy
sh '''
jira-cli release create \
  --project PROJ \
  --name ${APP_VERSION} \
  --release-date ${RELEASE_DATE}
'''
```

Then:

```groovy
sh '''
jira-cli artifact upload ${JIRA_ISSUE} \
  --file build/application-${APP_VERSION}.zip
'''
```

## GitLab CI Example

```yaml
release:
  stage: release
  script:
    - jira-cli release create
        --project "$JIRA_PROJECT"
        --name "$CI_COMMIT_TAG"
```

Artifact upload:

```yaml
upload:
  stage: deploy
  script:
    - jira-cli artifact upload "$JIRA_ISSUE"
        --file "build/application.zip"
```

---

# 17. Output Formats

The CLI should support multiple output formats.

## Table

Default:

```bash
jira-cli release list --project PROJ
```

Output:

```text
NAME       RELEASE DATE     RELEASED
--------------------------------------
v1.0.0     2026-06-01       yes
v1.1.0     2026-07-01       yes
v1.2.0     2026-08-20       no
```

## JSON

```bash
jira-cli release list \
  --project PROJ \
  --output json
```

Output:

```json
[
  {
    "id": "10001",
    "name": "v1.2.0",
    "released": false,
    "release_date": "2026-08-20"
  }
]
```

## Quiet Mode

For CI/CD:

```bash
jira-cli release create \
  --project PROJ \
  --name v1.2.0 \
  --quiet
```

Output:

```text
10001
```

---

# 18. Dry Run

All destructive or modifying operations should support:

```bash
--dry-run
```

Example:

```bash
jira-cli release create \
  --project PROJ \
  --name v2.0.0 \
  --dry-run
```

Output:

```text
DRY RUN

No changes will be made.

Operation:
Create Jira Release

Project:
PROJ

Version:
v2.0.0
```

This is particularly important for CI/CD environments.

---

# 19. Error Handling

The CLI should provide meaningful errors.

Example:

```text
ERROR: Jira authentication failed.

HTTP Status: 401

Please verify:
- JIRA_URL
- JIRA_EMAIL
- JIRA_API_TOKEN
```

Permission error:

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

# 20. Exit Codes

The CLI should use standard exit codes.

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
```

This allows CI/CD systems to determine whether an operation succeeded.

---

# 21. Logging

Logging levels:

```text
ERROR
WARNING
INFO
DEBUG
```

Example:

```bash
jira-cli release create \
  --project PROJ \
  --name v1.2.0 \
  --verbose
```

Debug output:

```text
DEBUG: Jira URL: https://company.atlassian.net
DEBUG: Request: POST /rest/api/3/version
DEBUG: Project: PROJ
DEBUG: Version: v1.2.0
DEBUG: Response: 201
```

Secrets must never appear in logs.

---

# 22. Security Requirements

## Credential Protection

Never allow:

```bash
jira-cli --token abc123
```

to appear in normal command history where avoidable.

Preferred:

```bash
JIRA_API_TOKEN=xxxxx
```

or a secure credential store.

## Token Masking

Logs must mask tokens:

```text
JIRA_API_TOKEN=********
```

## TLS

HTTPS must be used for production Jira instances.

Certificate verification should be enabled by default.

An insecure option may be provided only for development:

```bash
--no-verify-ssl
```

This option should display a warning.

---

# 23. API Client Design

The Jira API client should abstract HTTP communication.

Example conceptual interface:

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

Services should use this client instead of directly using `httpx`.

Example:

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

This makes testing easier.

---

# 24. Service Layer

## ReleaseService

Responsibilities:

```text
list_releases()
get_release()
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

---

# 25. Validation

The CLI should validate input before making API calls.

Examples:

### Project

```text
PROJ
```

Valid.

```text
project name with spaces
```

Should be rejected where a project key is required.

### Jira Issue

```text
PROJ-123
```

Valid.

### Release

Release name cannot be empty.

### Artifact

The file must:

- Exist
- Be readable
- Be a regular file
- Be within configured size limits where known

---

# 26. Command Groups

The initial CLI should expose:

```text
jira-cli
│
├── config
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
│   ├── list
│   ├── get
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

# 27. MVP Scope

The first release should remain small.

## MVP Features

### Authentication

- [ ] Jira URL configuration
- [ ] Jira email configuration
- [ ] Jira API token
- [ ] Authentication validation

### Project

- [ ] List projects
- [ ] Get project

### Release

- [ ] List releases
- [ ] Get release
- [ ] Create release
- [ ] Update release
- [ ] Publish release

### Issue

- [ ] Get issue
- [ ] Search using JQL
- [ ] Add comment
- [ ] Update issue

### Artifact

- [ ] Upload artifact to Jira issue
- [ ] Upload multiple artifacts
- [ ] Validate file
- [ ] Display uploaded attachment information

### CLI

- [ ] Table output
- [ ] JSON output
- [ ] Quiet mode
- [ ] Verbose mode
- [ ] Dry-run mode
- [ ] Exit codes
- [ ] Error handling

---

# 28. Phase 2

After MVP:

- [ ] OAuth 2.0
- [ ] Configuration profiles
- [ ] YAML configuration
- [ ] Jira workflow automation
- [ ] Bulk issue operations
- [ ] Release automation
- [ ] Automatic release notes
- [ ] Git commit integration
- [ ] Git tag integration
- [ ] Jenkins integration helpers
- [ ] GitLab integration helpers

---

# 29. Phase 3

Advanced DevOps features:

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
  --version v2.5.0 \
  --issue PROJ-123 \
  --artifact ./build/application.zip \
  --environment production
```

This could perform:

1. Validate Jira connection.
2. Find/create release.
3. Upload artifact.
4. Add deployment comment.
5. Update Jira issue.
6. Transition issue if configured.
7. Return success/failure status.

---

# 30. Release Automation

A future high-level command:

```bash
jira-cli release prepare \
  --project PROJ \
  --version v2.5.0 \
  --artifact ./build/application.zip
```

The CLI would:

```text
1. Authenticate with Jira
2. Validate project
3. Check whether version exists
4. Create version if missing
5. Find related Jira issues
6. Upload artifact
7. Add release comment
8. Generate release information
9. Return release ID
```

---

# 31. Example End-to-End Workflow

Developer creates a Git tag:

```bash
git tag v1.5.0
git push origin v1.5.0
```

CI/CD pipeline starts.

Build:

```bash
./gradlew build
```

Jira release:

```bash
jira-cli release create \
  --project PROJ \
  --name v1.5.0
```

Artifact:

```bash
jira-cli artifact upload PROJ-123 \
  --file build/application-1.5.0.zip
```

Comment:

```bash
jira-cli issue comment PROJ-123 \
  --message "Build v1.5.0 uploaded successfully."
```

Publish:

```bash
jira-cli release publish "$RELEASE_ID"
```

Result:

```text
========================================
JIRA RELEASE COMPLETED
========================================

Project       : PROJ
Release       : v1.5.0
Release ID    : 10042
Artifact      : application-1.5.0.zip
Issue         : PROJ-123
Status        : SUCCESS
========================================
```

---

# 32. API Version Strategy

The application should isolate Jira API endpoint paths inside the Jira client/service layer.

For Jira Cloud, the initial implementation should target REST API v3 where supported. Jira's current REST documentation exposes project version and attachment operations through v3 endpoints.

Avoid spreading URLs such as:

```text
/rest/api/3/...
```

throughout the application.

Instead:

```python
JIRA_API_VERSION = "3"
```

and centralize endpoint construction.

---

# 33. Testing Strategy

## Unit Tests

Test:

- Authentication
- Request construction
- Release creation
- Release update
- Issue search
- Issue comments
- Artifact validation
- Artifact upload
- Error handling

## Integration Tests

Integration tests should run against a test Jira project.

Example:

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

## Mock API Tests

Most unit tests should mock Jira API responses to avoid dependency on a live Jira environment.

---

# 34. CI/CD

The project itself should use CI/CD.

Pipeline stages:

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

# 35. Packaging

The CLI should be installable using:

```bash
pip install jira-cli
```

Then users can execute:

```bash
jira-cli --help
```

The package should expose:

```text
jira-cli
```

as the console entry point.

---

# 36. Help System

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
jira-cli release create --help
```

---

# 37. Success Criteria

The MVP will be considered successful when a user can:

1. Configure Jira credentials.
2. Verify Jira connectivity.
3. List Jira projects.
4. Search Jira issues.
5. Create a Jira release.
6. Update a Jira release.
7. Publish a Jira release.
8. Upload an artifact to a Jira issue.
9. Add a comment to an issue.
10. Run all of the above from Jenkins/GitLab CI.
11. Receive predictable exit codes.
12. Receive JSON output for automation.

---

# 38. Future Vision

The long-term goal is to make Jira CLI a **DevOps-focused Jira automation platform**.

Example:

```bash
jira-cli deploy \
    --project ERP \
    --version v3.2.0 \
    --environment production \
    --artifact ./dist/erp-3.2.0.zip
```

Behind the scenes:

```text
                  Jira CLI
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
    Release        Issues       Artifact
       |             |             |
       v             v             v
   Jira Version   Jira Issues   Attachment
       |             |             |
       +-------------+-------------+
                     |
                     v
               Deployment
```

This turns Jira CLI from a simple API wrapper into a reusable **Jira + CI/CD automation tool**.

---

# 39. Recommended Initial Milestones

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
- [ ] Quiet mode
- [ ] Exit codes
- [ ] Jenkins example
- [ ] GitLab CI example
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

# 40. Final Product Definition

**Jira CLI** is a Python command-line automation tool that provides a controlled and scriptable interface to Jira.

The core use case is:

```text
Developer / CI/CD
       |
       v
   jira-cli
       |
       +--> Jira Project
       |
       +--> Jira Issue
       |
       +--> Jira Release
       |
       +--> Jira Artifact
       |
       v
   Jira REST API
```

The MVP should focus on four capabilities:

```text
1. Jira Authentication
2. Jira Issue Management
3. Jira Release Management
4. Jira Artifact Upload
```

Once these are stable, the project can evolve into a broader **Jira DevOps CLI** supporting release automation, deployment tracking, Git integration, CI/CD integration, and automated Jira workflows.
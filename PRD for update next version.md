# Product Requirements Document (PRD)

## 1. Product Overview

### Product Name

**Jira CLI Release Automation**

### Product Type

Python-based Command Line Interface (CLI) for automating Jira release/version management and integrating release version generation into CI/CD pipelines.

### Primary Objective

The application will use the Jira REST API to:

1. Read the current Jira release/version.
2. Automatically calculate the next monthly release version.
3. Allow the user to optionally provide a custom release date.
4. Create the next release in Jira.
5. Return the new version to the CI/CD pipeline.
6. Allow CI/CD to use that version for application build and deployment.
7. Optionally update Jira issues and upload build artifacts.

---

# 2. Release Versioning Strategy

The default release version format is:

```text
YY.MM.DD
```

The default behavior uses the **last day of the month**.

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

The application automatically calculates the last day of the next month when the user does not provide a date.

---

# 3. Custom Release Date

The user may optionally provide a release date.

This is important because not every release will necessarily happen on the last day of the month.

## Default Behavior

If the user does not specify a date:

```bash
jira-cli release next --project PROJ
```

The CLI calculates the next monthly release.

Example:

```text
Current Release:
26.07.31

Next Month:
August 2026

Last Day:
31

Next Release:
26.08.31
```

---

## Custom Date Behavior

The user can provide a specific date:

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-25
```

The CLI will create/use:

```text
26.08.25
```

The CLI input date format should be:

```text
YYYY-MM-DD
```

The Jira release version remains:

```text
YY.MM.DD
```

### Example

Input:

```text
2026-08-25
```

Version:

```text
26.08.25
```

---

# 4. Date Selection Rules

The CLI must follow this priority:

```text
                 User provides --date?
                         |
              +----------+----------+
              |                     |
             YES                    NO
              |                     |
              v                     v
       Validate supplied       Calculate next
             date                 month
              |                     |
              v                     v
       YY.MM.DD version      Last day of month
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
YY.MM.LAST_DAY
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

### Rule 3 — Date Takes Priority

If `--date` is provided, the automatic last-day-of-month calculation must not be used.

---

# 5. Date Validation

The CLI must validate the supplied date.

Valid:

```text
2026-08-25
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

Invalid dates must produce a clear error:

```text
ERROR: Invalid release date.

Expected format:
YYYY-MM-DD

Example:
2026-08-25
```

---

# 6. Date and Version Relationship

The CLI must convert the supplied date into the Jira version format.

```text
CLI Date       Jira Version
--------------------------------
2026-08-25  ->  26.08.25
2026-08-31  ->  26.08.31
2026-09-15  ->  26.09.15
2027-01-31  ->  27.01.31
```

The application should maintain both values internally:

```json
{
  "release_date": "2026-08-25",
  "version": "26.08.25"
}
```

---

# 7. Current Release Command

Command:

```bash
jira-cli release current --project PROJ
```

The CLI retrieves Jira releases and identifies the latest valid release.

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

Example:

```json
{
  "project": "PROJ",
  "version": "26.07.31",
  "released": false
}
```

---

# 8. Next Release Command

The primary command is:

```bash
jira-cli release next --project PROJ
```

The CLI will:

1. Connect to Jira.
2. Retrieve project releases.
3. Identify the latest valid release.
4. Determine whether the user provided `--date`.
5. If no date was provided, calculate the next monthly release date.
6. If a date was provided, validate it.
7. Convert the date to `YY.MM.DD`.
8. Check whether the release already exists.
9. Create the release if it does not exist.
10. Return the release version and release ID.

---

# 9. Automatic Date Example

Current Jira release:

```text
26.07.31
```

Command:

```bash
jira-cli release next --project PROJ
```

The CLI calculates:

```text
Current:
2026-07-31

Next month:
2026-08

Last day:
2026-08-31

Version:
26.08.31
```

Result:

```text
Current Release : 26.07.31
Next Release    : 26.08.31
Status          : CREATED
```

---

# 10. Custom Date Example

Current Jira release:

```text
26.07.31
```

Command:

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-20
```

Result:

```text
Current Release : 26.07.31
Requested Date  : 2026-08-20
Next Release    : 26.08.20
Status          : CREATED
```

The CLI must not change the date to `26.08.31`.

The explicitly supplied date has priority.

---

# 11. Future-Date Example

The user may specify a date in a future month:

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

The CLI should allow this unless a future business rule explicitly restricts releases to the immediate next month.

---

# 12. Custom Date and Existing Release

Before creating a release, the CLI must check Jira.

Example:

```text
Requested Version:
26.08.20

Jira:
26.08.20 already exists
```

The CLI must not create a duplicate.

Result:

```text
Release 26.08.20 already exists.

Release ID: 10042
```

CI/CD should still receive:

```text
26.08.20
```

JSON:

```json
{
  "project": "PROJ",
  "previous_release": "26.07.31",
  "next_release": "26.08.20",
  "release_id": "10042",
  "created": false,
  "existing": true
}
```

---

# 13. Version-Only Output

For CI/CD, the recommended command is:

```bash
jira-cli release next \
    --project PROJ \
    --output version
```

Default automatic date:

```text
26.08.31
```

Custom date:

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

This allows the CI/CD pipeline to easily capture the release version.

---

# 14. JSON Output

Command:

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-20 \
    --output json
```

Output:

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

For automatic date:

```bash
jira-cli release next \
    --project PROJ \
    --output json
```

Output:

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

# 15. Dry Run

Both automatic and custom dates must support dry-run.

Automatic:

```bash
jira-cli release next \
    --project PROJ \
    --dry-run
```

Custom:

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-20 \
    --dry-run
```

Example:

```text
DRY RUN

Current Release : 26.07.31
Release Date    : 2026-08-20
Next Release    : 26.08.20

No changes will be made to Jira.
```

---

# 16. CI/CD Integration

The CLI is primarily designed to run from CI/CD pipelines.

Recommended workflow:

```text
CI/CD
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
  +--> Create release
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

# 17. Jenkins Example — Automatic Date

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

If the current release is:

```text
26.07.31
```

the pipeline receives:

```text
APP_VERSION=26.08.31
```

---

# 18. Jenkins Example — Custom Date

The pipeline can provide a release date:

```groovy
parameters {
    string(
        name: 'RELEASE_DATE',
        defaultValue: '',
        description: 'Optional release date in YYYY-MM-DD format'
    )
}
```

Then:

```groovy
stage('Create Jira Release') {
    steps {
        script {
            def dateOption = ''

            if (params.RELEASE_DATE?.trim()) {
                dateOption = "--date ${params.RELEASE_DATE}"
            }

            env.APP_VERSION = sh(
                script: """
                    jira-cli release next \
                        --project "$JIRA_PROJECT" \
                        ${dateOption} \
                        --output version
                """,
                returnStdout: true
            ).trim()

            echo "Application Version: ${env.APP_VERSION}"
        }
    }
}
```

The Jenkins user can enter:

```text
2026-08-20
```

and the pipeline receives:

```text
APP_VERSION=26.08.20
```

---

# 19. GitLab CI Example

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

# 20. Recommended CLI Syntax

The final CLI syntax should be:

```text
jira-cli release current
jira-cli release next
jira-cli release create
```

Options for `release next`:

```text
--project
--date
--output
--dry-run
--verbose
```

Example:

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-20 \
    --output version
```

---

# 21. Command Behavior Matrix

| Command                             | Date         | Behavior                            |
| ----------------------------------- | ------------ | ----------------------------------- |
| `release next`                      | Not provided | Calculate last day of next month    |
| `release next --date 2026-08-20`    | Provided     | Use `26.08.20`                      |
| `release next --date 2026-08-31`    | Provided     | Use `26.08.31`                      |
| `release next --date 2026-02-30`    | Invalid      | Fail validation                     |
| `release next --dry-run`            | Not provided | Calculate but don't create          |
| `release next --date ... --dry-run` | Provided     | Validate/calculate but don't create |

---

# 22. Release Date Rules

The application must distinguish between:

### Automatic Release Date

Used when the user does not specify a date:

```text
Last day of next month
```

### Explicit Release Date

Used when the user provides:

```text
--date YYYY-MM-DD
```

The explicit date always takes priority.

---

# 23. Recommended Business Rule

The CLI should **not automatically modify a user-provided date**.

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

It must not change it to:

```text
26.08.31
```

The last-day-of-month rule applies only when `--date` is omitted.

---

# 24. MVP Scope

## Authentication

* [ ] Jira URL
* [ ] Jira email
* [ ] Jira API token
* [ ] Connection test

## Release Management

* [ ] Read current release
* [ ] Identify latest valid CalVer release
* [ ] Calculate next monthly release
* [ ] Support optional custom date
* [ ] Validate custom date
* [ ] Convert date to `YY.MM.DD`
* [ ] Check duplicate release
* [ ] Create release
* [ ] Return release ID
* [ ] Return release version

## CLI

* [ ] Human-readable output
* [ ] JSON output
* [ ] Version-only output
* [ ] Dry-run
* [ ] Verbose logging
* [ ] Exit codes
* [ ] Error handling

## CI/CD

* [ ] Jenkins integration example
* [ ] GitLab CI integration example
* [ ] Azure DevOps integration example
* [ ] Environment variable support

---

# 25. Future Features

After the MVP:

* [ ] Jira issue management
* [ ] Jira comments
* [ ] Artifact upload
* [ ] JFrog Artifactory integration
* [ ] Deployment tracking
* [ ] Git integration
* [ ] Automatic release notes
* [ ] Docker image support
* [ ] OAuth 2.0
* [ ] AWS Secrets Manager
* [ ] HashiCorp Vault
* [ ] Jira Data Center support
* [ ] Multiple Jira profiles
* [ ] Release approval workflow

---

# 26. Final Product Workflow

The final MVP workflow is:

```text
                     CI/CD Pipeline
                           |
                           v
                 jira-cli release next
                           |
                 +---------+---------+
                 |                   |
          --date provided?       No --date
                 |                   |
                YES                  NO
                 |                   |
                 v                   v
          Validate date       Read current release
                 |                   |
                 v                   v
          Convert date        Calculate next month
          to YY.MM.DD         Last day of month
                 |                   |
                 +---------+---------+
                           |
                           v
                    Check Jira
                           |
                  +--------+--------+
                  |                 |
               Exists            Missing
                  |                 |
                  v                 v
             Use existing       Create release
                  |                 |
                  +--------+--------+
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
                        Deploy
```

### Example 1 — Normal Monthly Release

```bash
jira-cli release next --project PROJ --output version
```

Result:

```text
26.08.31
```

### Example 2 — Custom Release Date

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-20 \
    --output version
```

Result:

```text
26.08.20
```

### Example 3 — Preview

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-20 \
    --dry-run
```

Result:

```text
Current Release : 26.07.31
Release Date    : 2026-08-20
Next Release    : 26.08.20

No changes will be made to Jira.
```

---

# 27. Success Criteria

The MVP will be considered successful when the following works reliably:

```bash
jira-cli release next --project PROJ --output version
```

and automatically performs:

```text
Read Jira
    ↓
Find latest YY.MM.DD release
    ↓
Calculate next month
    ↓
Calculate last day of month
    ↓
Generate YY.MM.DD
    ↓
Check Jira
    ↓
Create release if required
    ↓
Return version
```

And when the user provides a date:

```bash
jira-cli release next \
    --project PROJ \
    --date 2026-08-20 \
    --output version
```

the CLI must:

```text
Validate date
    ↓
Convert 2026-08-20
    ↓
26.08.20
    ↓
Check Jira
    ↓
Create/use release
    ↓
Return 26.08.20
```

The CI/CD pipeline can then use the returned version:

```text
APP_VERSION=26.08.20
```

and continue:

```text
Build
  ↓
Package
  ↓
Deploy
```

---

# 28. Product Principle

The core principle of the Jira CLI is:

> **Automate Jira release creation while allowing CI/CD users to either use the standard monthly release date or explicitly choose a release date when required.**

Default:

```text
YY.MM.LAST_DAY_OF_MONTH
```

Override:

```text
--date YYYY-MM-DD
```

This provides automation for normal monthly releases while retaining flexibility for exceptional or scheduled deployments.

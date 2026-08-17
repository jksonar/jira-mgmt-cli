"""Exception hierarchy for Jira CLI, each carrying the exit code it maps to."""


class JiraCliError(Exception):
    """Base error for all Jira CLI failures."""

    exit_code = 1

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ConfigurationError(JiraCliError):
    """Missing or invalid configuration (e.g. env vars)."""

    exit_code = 3


class AuthenticationError(JiraCliError):
    """Jira rejected the credentials (HTTP 401)."""

    exit_code = 3


class AuthorizationError(JiraCliError):
    """Jira rejected the operation due to insufficient permissions (HTTP 403)."""

    exit_code = 4


class NotFoundError(JiraCliError):
    """Requested Jira resource does not exist (HTTP 404)."""

    exit_code = 5


class ValidationError(JiraCliError):
    """Jira rejected the request as invalid (HTTP 400/422), or a local domain guard failed."""

    exit_code = 6


class NetworkError(JiraCliError):
    """Network/connection failure, or an unmapped/server-side HTTP error."""

    exit_code = 7


class ArtifactError(JiraCliError):
    """File/artifact failure. Reserved for future artifact commands."""

    exit_code = 8


class ReleaseCreationError(JiraCliError):
    """The calculated next release could not be created in Jira."""

    exit_code = 8

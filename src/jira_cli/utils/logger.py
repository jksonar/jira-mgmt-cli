"""Logging setup for Jira CLI, with secret masking for verbose/debug output."""

from __future__ import annotations

import logging

_ROOT_LOGGER_NAME = "jira_cli"
_secrets: list[str] = []


class SecretMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for secret in _secrets:
            if secret:
                message = message.replace(secret, "********")
        record.msg = message
        record.args = ()
        return True


def configure_logging(verbose: bool) -> None:
    root_logger = logging.getLogger(_ROOT_LOGGER_NAME)
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    handler.addFilter(SecretMaskingFilter())

    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    root_logger.propagate = False


def mask_secret(secret: str) -> None:
    if secret and secret not in _secrets:
        _secrets.append(secret)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")

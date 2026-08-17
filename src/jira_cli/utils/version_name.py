"""Version name cleanup: strips a token out of a release name, matching the
`clean-version-name` behavior of the legacy `devops-jrmt` Node.js tool."""

from __future__ import annotations

import re


def clean_version_name(raw_name: str, token: str | None = None) -> str:
    """Strip `token` out of `raw_name` and tidy up the result.

    Mirrors devops-jrmt's `cleanVersionName`:
    1. Trim whitespace.
    2. Remember whether the trimmed name contained a `/` before stripping.
    3. Strip the token in three passes (in order): "/<token>", "<token>/",
       then the bare token — each pass removes all occurrences.
    4. Collapse repeated `/` into one.
    5. Strip a single trailing `/`.
    6. If the name has no `/` left AND never had one before stripping,
       truncate everything from the first `-` onward.
    """
    if not isinstance(raw_name, str):
        raise TypeError("Version name must be a string")

    name = raw_name.strip()
    had_slash_before_strip = "/" in name

    if token is not None:
        if not isinstance(token, str) or len(token) == 0:
            raise ValueError("Token to strip must be a non-empty string when provided")
        escaped = re.escape(token)
        name = re.sub(f"/{escaped}", "", name)
        name = re.sub(f"{escaped}/", "", name)
        name = re.sub(escaped, "", name)

    name = re.sub(r"/{2,}", "/", name)

    if name.endswith("/"):
        name = name[:-1].rstrip()

    if "/" not in name and not had_slash_before_strip:
        dash_index = name.find("-")
        if dash_index != -1:
            name = name[:dash_index].strip()

    return name

"""
Yaegi Go Compatibility Datasource Generator

Fetches the `go` directive from Yaegi's go.mod to track
the maximum Go version supported by Yaegi (used by Traefik plugins).

This is consumed as a Renovate custom datasource to constrain
Go version bumps in plugin go.mod files.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests

YAEGI_GOMOD_URL = "https://raw.githubusercontent.com/traefik/yaegi/master/go.mod"
YAEGI_RELEASES_URL = "https://api.github.com/repos/traefik/yaegi/releases"

# Match the go directive line in go.mod, e.g. "go 1.21"
GO_DIRECTIVE_PATTERN = re.compile(r"^go\s+(\d+\.\d+)", re.MULTILINE)


@dataclass
class GoCompatRelease:
    """Represents a Go compatibility version from Yaegi."""

    version: str
    release_timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        result = {"version": self.version}
        if self.release_timestamp:
            result["releaseTimestamp"] = self.release_timestamp
        return result


def fetch_gomod_content(url: str = YAEGI_GOMOD_URL, timeout: int = 30) -> str:
    """Fetch the go.mod file content from Yaegi's repository."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def extract_go_version(gomod_content: str) -> Optional[str]:
    """Extract the go directive version from go.mod content."""
    match = GO_DIRECTIVE_PATTERN.search(gomod_content)
    if match:
        return match.group(1)
    return None


def fetch_yaegi_releases(url: str = YAEGI_RELEASES_URL, timeout: int = 30) -> list[dict]:
    """Fetch Yaegi releases from GitHub API to get timestamps."""
    response = requests.get(url, timeout=timeout, params={"per_page": 100})
    response.raise_for_status()
    return response.json()


def fetch_yaegi_go_compat() -> dict:
    """
    Fetch the Go compatibility version from Yaegi's go.mod.

    Returns a Renovate custom datasource with the supported Go version(s).
    The version represents the maximum Go minor version that Yaegi supports.
    Traefik plugin go.mod files should not exceed this version.
    """
    gomod_content = fetch_gomod_content()
    go_version = extract_go_version(gomod_content)

    if not go_version:
        raise ValueError("Could not extract go directive from Yaegi go.mod")

    # Use current time as release timestamp since we track the latest state
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    release = GoCompatRelease(version=go_version, release_timestamp=timestamp)

    return {"releases": [release.to_dict()]}

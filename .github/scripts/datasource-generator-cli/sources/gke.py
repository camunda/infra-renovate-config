"""
GKE Release Channel Datasource Generator

Fetches GKE versions from GKE release channel RSS feeds
and generates Renovate-compatible custom datasource JSON files.

Supports all GKE release channels: rapid, regular, stable, extended.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import requests

# Regex pattern for GKE versions (e.g., 1.31.2-gke.1234)
GKE_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+-gke\.\d+")


class GKEChannel(str, Enum):
    """GKE release channels."""

    RAPID = "rapid"
    REGULAR = "regular"
    STABLE = "stable"
    EXTENDED = "extended"

    @property
    def feed_url(self) -> str:
        """Get the RSS feed URL for this channel."""
        return f"https://cloud.google.com/feeds/gke-{self.value}-channel-release-notes.xml"

    @property
    def description(self) -> str:
        """Get human-readable description."""
        descriptions = {
            GKEChannel.RAPID: "GKE Rapid channel - newest features, updated weekly",
            GKEChannel.REGULAR: "GKE Regular channel - balance of features and stability",
            GKEChannel.STABLE: "GKE Stable channel - production-ready, well-tested",
            GKEChannel.EXTENDED: "GKE Extended channel - longest support window",
        }
        return descriptions[self]


@dataclass
class Release:
    """Represents a GKE release version."""

    version: str
    release_timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to Renovate release format."""
        result = {"version": self.version}
        if self.release_timestamp:
            result["releaseTimestamp"] = self.release_timestamp
        return result


def fetch_feed(url: str, timeout: int = 30) -> str:
    """Fetch the RSS feed content."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_atom_date(date_str: str) -> Optional[str]:
    """Parse Atom date format to ISO 8601."""
    try:
        # Atom dates are already ISO 8601 format
        # Just validate and normalize
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, AttributeError):
        return None


def extract_versions_from_feed(feed_content: str) -> list[Release]:
    """
    Extract GKE versions from the Atom feed content.

    Returns a list of Release objects with version and optional timestamp.
    """
    releases = []
    seen_versions = set()

    # Parse the Atom feed
    root = ET.fromstring(feed_content)

    # Atom namespace
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    # Find all entry elements
    for entry in root.findall("atom:entry", ns):
        # Get the updated timestamp
        updated_elem = entry.find("atom:updated", ns)
        timestamp = None
        if updated_elem is not None and updated_elem.text:
            timestamp = parse_atom_date(updated_elem.text)

        # Get the title and content to search for versions
        title_elem = entry.find("atom:title", ns)
        content_elem = entry.find("atom:content", ns)

        search_text = ""
        if title_elem is not None and title_elem.text:
            search_text += title_elem.text + " "
        if content_elem is not None and content_elem.text:
            search_text += content_elem.text

        # Extract all versions from the entry
        versions = GKE_VERSION_PATTERN.findall(search_text)

        for version in versions:
            if version not in seen_versions:
                seen_versions.add(version)
                releases.append(Release(version=version, release_timestamp=timestamp))

    return releases


def sort_versions(releases: list[Release]) -> list[Release]:
    """
    Sort releases by version in descending order (newest first).

    Uses semantic versioning with GKE build number.
    """

    def version_key(release: Release) -> tuple:
        """Extract version components for sorting."""
        match = re.match(r"(\d+)\.(\d+)\.(\d+)-gke\.(\d+)", release.version)
        if match:
            return tuple(int(x) for x in match.groups())
        return (0, 0, 0, 0)

    return sorted(releases, key=version_key, reverse=True)


def generate_datasource(releases: list[Release]) -> dict:
    """Generate the Renovate custom datasource JSON structure."""
    return {"releases": [r.to_dict() for r in releases]}


def fetch_gke_versions(channel: GKEChannel) -> dict:
    """
    Fetch and generate GKE datasource for a specific channel.

    Args:
        channel: The GKE release channel to fetch versions from.

    Returns:
        A dict ready to be serialized to JSON.
    """
    feed_content = fetch_feed(channel.feed_url)
    releases = extract_versions_from_feed(feed_content)
    sorted_releases = sort_versions(releases)
    return generate_datasource(sorted_releases)

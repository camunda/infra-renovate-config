"""
GKE Release Channel Datasource Generator

Generates Renovate-compatible custom datasource JSON files for the GKE release
channels: rapid, regular, stable, extended.

Two inputs are combined:

- The GKE Container API (``getServerConfig``) is the authoritative list of the
  versions a channel actually offers.
- The release-notes Atom feed only supplies ``releaseTimestamp`` metadata and
  historical versions the API no longer advertises.

The feed alone is not trustworthy: it is a docs artifact that has silently
frozen for weeks at a time while GKE kept shipping versions. Staleness of the
merged result is reported by the caller (see ``staleness``).
"""

import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import requests

# Regex pattern for GKE versions (e.g., 1.31.2-gke.1234)
GKE_VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+-gke\.\d+")

# Authoritative per-channel version list (validVersions + defaultVersion).
CONTAINER_SERVER_CONFIG_URL = "https://container.googleapis.com/v1/projects/{project}/locations/{location}/serverConfig"


class GKEChannel(str, Enum):
    """GKE release channels."""

    RAPID = "rapid"
    REGULAR = "regular"
    STABLE = "stable"
    EXTENDED = "extended"

    @property
    def feed_url(self) -> str:
        """Get the RSS feed URL for this channel.

        Uses docs.cloud.google.com directly to avoid an unreliable 301 redirect
        from cloud.google.com that intermittently resolves to an HTML page instead.
        """
        return f"https://docs.cloud.google.com/feeds/gke-{self.value}-channel-release-notes.xml"

    @property
    def api_channel(self) -> str:
        """Get the channel name as reported by the Container API."""
        return self.value.upper()

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


def fetch_feed(url: str, timeout: int = 30, max_retries: int = 3) -> str:
    """Fetch the RSS feed content, with retry logic for transient failures.

    The GKE feed URL at cloud.google.com occasionally returns an HTML page
    instead of XML (HTTP 200, content-type text/html). This function validates
    the content-type and retries on such failures.
    """
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "xml" not in content_type:
                raise ValueError(
                    f"Unexpected content-type '{content_type}' (expected XML). "
                    f"Response body starts with: {repr(response.content[:200])}"
                )
            return response.text
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                print(
                    f"  Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {wait_time}s...",
                    file=sys.stderr,
                )
                time.sleep(wait_time)
    raise last_exc


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


def fetch_channel_versions_from_api(
    channel: GKEChannel,
    project: str,
    location: str,
    timeout: int = 30,
) -> list[str]:
    """
    Fetch the versions a channel currently offers from the GKE Container API.

    This is the authoritative source. Requires Application Default Credentials
    with the ``container.getServerConfig`` permission (roles/container.viewer).
    """
    # Imported lazily so the module stays importable without GCP credentials.
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    session = AuthorizedSession(credentials)

    url = CONTAINER_SERVER_CONFIG_URL.format(project=project, location=location)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    for entry in payload.get("channels", []):
        if entry.get("channel") != channel.api_channel:
            continue

        versions = list(entry.get("validVersions", []))
        default_version = entry.get("defaultVersion")
        if default_version and default_version not in versions:
            versions.append(default_version)
        return [v for v in versions if GKE_VERSION_PATTERN.fullmatch(v)]

    raise ValueError(f"Channel {channel.api_channel} not found in serverConfig for {project}/{location}")


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


def fetch_gke_versions(
    channel: GKEChannel,
    project: Optional[str] = None,
    location: Optional[str] = None,
) -> dict:
    """
    Fetch and generate the GKE datasource for a specific channel.

    The Container API provides the authoritative version list; the feed adds
    release timestamps and older versions the API no longer advertises.

    Args:
        channel: The GKE release channel to fetch versions from.
        project: GCP project used to call the Container API. Without it the
            feed is the only source.
        location: GCP location (region) used to call the Container API.

    Returns:
        A dict ready to be serialized to JSON.
    """
    feed_content = fetch_feed(channel.feed_url)
    releases = extract_versions_from_feed(feed_content)

    if project and location:
        api_versions = fetch_channel_versions_from_api(channel, project, location)
        known = {release.version for release in releases}
        missing = [version for version in api_versions if version not in known]

        releases.extend(Release(version=version) for version in missing)
        print(f"  Container API reports {len(api_versions)} version(s) for channel {channel.api_channel}")

        if missing:
            print(f"  Added {len(missing)} version(s) absent from the feed: {', '.join(sorted(missing))}")

    sorted_releases = sort_versions(releases)
    return generate_datasource(sorted_releases)

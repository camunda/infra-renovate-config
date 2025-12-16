"""
Tests for GKE release channel datasource generator.
"""

import pytest

from sources.gke import (
    GKE_VERSION_PATTERN,
    GKEChannel,
    Release,
    extract_versions_from_feed,
    generate_datasource,
    parse_atom_date,
    sort_versions,
)


class TestGKEChannel:
    """Tests for GKEChannel enum."""

    def test_channel_feed_urls(self):
        """Test that each channel has correct feed URL."""
        assert GKEChannel.RAPID.feed_url == "https://cloud.google.com/feeds/gke-rapid-channel-release-notes.xml"
        assert GKEChannel.REGULAR.feed_url == "https://cloud.google.com/feeds/gke-regular-channel-release-notes.xml"
        assert GKEChannel.STABLE.feed_url == "https://cloud.google.com/feeds/gke-stable-channel-release-notes.xml"
        assert GKEChannel.EXTENDED.feed_url == "https://cloud.google.com/feeds/gke-extended-channel-release-notes.xml"

    def test_channel_values(self):
        """Test channel string values."""
        assert GKEChannel.RAPID.value == "rapid"
        assert GKEChannel.REGULAR.value == "regular"
        assert GKEChannel.STABLE.value == "stable"
        assert GKEChannel.EXTENDED.value == "extended"

    def test_channel_descriptions(self):
        """Test that each channel has a description."""
        for channel in GKEChannel:
            assert channel.description is not None
            assert len(channel.description) > 0


class TestVersionPattern:
    """Tests for the GKE version regex pattern."""

    @pytest.mark.parametrize(
        "version",
        [
            "1.31.2-gke.1234",
            "1.30.0-gke.1",
            "1.33.5-gke.1791000",
            "2.0.0-gke.100",
        ],
    )
    def test_valid_versions(self, version: str):
        """Test that valid GKE versions are matched."""
        assert GKE_VERSION_PATTERN.match(version) is not None

    @pytest.mark.parametrize(
        "version",
        [
            "1.31.2",  # Missing -gke suffix
            "1.31-gke.1234",  # Missing patch version
            "v1.31.2-gke.1234",  # Has v prefix
            "1.31.2-gke",  # Missing build number
            "latest",
            "",
        ],
    )
    def test_invalid_versions(self, version: str):
        """Test that invalid versions are not matched."""
        assert GKE_VERSION_PATTERN.match(version) is None


class TestParseAtomDate:
    """Tests for Atom date parsing."""

    def test_parse_valid_date_with_z(self):
        """Test parsing date with Z suffix."""
        result = parse_atom_date("2025-01-15T10:30:00Z")
        assert result == "2025-01-15T10:30:00Z"

    def test_parse_valid_date_with_offset(self):
        """Test parsing date with timezone offset."""
        result = parse_atom_date("2025-01-15T10:30:00+00:00")
        assert result == "2025-01-15T10:30:00Z"

    def test_parse_invalid_date(self):
        """Test parsing invalid date returns None."""
        assert parse_atom_date("invalid") is None
        assert parse_atom_date("") is None

    def test_parse_none(self):
        """Test parsing None returns None."""
        assert parse_atom_date(None) is None


class TestExtractVersionsFromFeed:
    """Tests for feed parsing."""

    SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>GKE Rapid Channel Release Notes</title>
  <entry>
    <title>1.31.2-gke.1234 is now available</title>
    <updated>2025-01-15T10:00:00Z</updated>
    <content>Version 1.31.2-gke.1234 includes bug fixes.</content>
  </entry>
  <entry>
    <title>Multiple versions released</title>
    <updated>2025-01-10T08:00:00Z</updated>
    <content>Versions 1.30.5-gke.100 and 1.29.8-gke.200 are available.</content>
  </entry>
</feed>"""

    def test_extract_versions(self):
        """Test extracting versions from feed."""
        releases = extract_versions_from_feed(self.SAMPLE_FEED)

        versions = [r.version for r in releases]
        assert "1.31.2-gke.1234" in versions
        assert "1.30.5-gke.100" in versions
        assert "1.29.8-gke.200" in versions

    def test_extract_timestamps(self):
        """Test that timestamps are extracted."""
        releases = extract_versions_from_feed(self.SAMPLE_FEED)

        # Find the 1.31.2 release
        release = next(r for r in releases if r.version == "1.31.2-gke.1234")
        assert release.release_timestamp == "2025-01-15T10:00:00Z"

    def test_no_duplicates(self):
        """Test that duplicate versions are not included."""
        feed_with_duplicates = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>1.31.2-gke.1234</title>
    <updated>2025-01-15T10:00:00Z</updated>
    <content>Version 1.31.2-gke.1234</content>
  </entry>
  <entry>
    <title>Also 1.31.2-gke.1234</title>
    <updated>2025-01-14T10:00:00Z</updated>
    <content>Same version 1.31.2-gke.1234</content>
  </entry>
</feed>"""

        releases = extract_versions_from_feed(feed_with_duplicates)
        versions = [r.version for r in releases]
        assert versions.count("1.31.2-gke.1234") == 1


class TestSortVersions:
    """Tests for version sorting."""

    def test_sort_by_major(self):
        """Test sorting by major version."""
        releases = [
            Release("1.30.0-gke.100"),
            Release("2.0.0-gke.100"),
            Release("1.31.0-gke.100"),
        ]
        sorted_releases = sort_versions(releases)
        versions = [r.version for r in sorted_releases]
        assert versions == ["2.0.0-gke.100", "1.31.0-gke.100", "1.30.0-gke.100"]

    def test_sort_by_minor(self):
        """Test sorting by minor version."""
        releases = [
            Release("1.30.0-gke.100"),
            Release("1.31.0-gke.100"),
            Release("1.29.0-gke.100"),
        ]
        sorted_releases = sort_versions(releases)
        versions = [r.version for r in sorted_releases]
        assert versions == ["1.31.0-gke.100", "1.30.0-gke.100", "1.29.0-gke.100"]

    def test_sort_by_patch(self):
        """Test sorting by patch version."""
        releases = [
            Release("1.31.1-gke.100"),
            Release("1.31.3-gke.100"),
            Release("1.31.2-gke.100"),
        ]
        sorted_releases = sort_versions(releases)
        versions = [r.version for r in sorted_releases]
        assert versions == ["1.31.3-gke.100", "1.31.2-gke.100", "1.31.1-gke.100"]

    def test_sort_by_build(self):
        """Test sorting by GKE build number."""
        releases = [
            Release("1.31.2-gke.100"),
            Release("1.31.2-gke.1000"),
            Release("1.31.2-gke.500"),
        ]
        sorted_releases = sort_versions(releases)
        versions = [r.version for r in sorted_releases]
        assert versions == ["1.31.2-gke.1000", "1.31.2-gke.500", "1.31.2-gke.100"]


class TestGenerateDatasource:
    """Tests for datasource generation."""

    def test_generate_empty(self):
        """Test generating datasource with no releases."""
        result = generate_datasource([])
        assert result == {"releases": []}

    def test_generate_with_releases(self):
        """Test generating datasource with releases."""
        releases = [
            Release("1.31.2-gke.1234", "2025-01-15T10:00:00Z"),
            Release("1.30.5-gke.100"),
        ]
        result = generate_datasource(releases)

        assert len(result["releases"]) == 2
        assert result["releases"][0] == {
            "version": "1.31.2-gke.1234",
            "releaseTimestamp": "2025-01-15T10:00:00Z",
        }
        assert result["releases"][1] == {"version": "1.30.5-gke.100"}


class TestRelease:
    """Tests for Release dataclass."""

    def test_to_dict_with_timestamp(self):
        """Test converting release with timestamp to dict."""
        release = Release("1.31.2-gke.1234", "2025-01-15T10:00:00Z")
        result = release.to_dict()
        assert result == {
            "version": "1.31.2-gke.1234",
            "releaseTimestamp": "2025-01-15T10:00:00Z",
        }

    def test_to_dict_without_timestamp(self):
        """Test converting release without timestamp to dict."""
        release = Release("1.31.2-gke.1234")
        result = release.to_dict()
        assert result == {"version": "1.31.2-gke.1234"}

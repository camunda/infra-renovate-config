"""
Tests for datasource JSON schema validation.
"""

import json

import pytest


def validate_datasource_schema(data: dict) -> list[str]:
    """
    Validate that the datasource follows the expected Renovate schema.

    Returns a list of validation errors (empty if valid).
    """
    errors = []

    # Must have releases key
    if "releases" not in data:
        errors.append("Missing 'releases' key")
        return errors

    releases = data["releases"]

    # releases must be a list
    if not isinstance(releases, list):
        errors.append("'releases' must be a list")
        return errors

    # Validate each release
    for i, release in enumerate(releases):
        if not isinstance(release, dict):
            errors.append(f"Release at index {i} must be an object")
            continue

        # version is required
        if "version" not in release:
            errors.append(f"Release at index {i} missing 'version' key")
        elif not isinstance(release["version"], str):
            errors.append(f"Release at index {i} 'version' must be a string")
        elif not release["version"]:
            errors.append(f"Release at index {i} 'version' must not be empty")

        # releaseTimestamp is optional but must be ISO 8601 if present
        if "releaseTimestamp" in release:
            ts = release["releaseTimestamp"]
            if not isinstance(ts, str):
                errors.append(f"Release at index {i} 'releaseTimestamp' must be a string")
            elif ts and not _is_valid_iso8601(ts):
                errors.append(f"Release at index {i} 'releaseTimestamp' must be ISO 8601 format")

    return errors


def _is_valid_iso8601(timestamp: str) -> bool:
    """Check if timestamp is valid ISO 8601 format."""
    import re

    # Basic ISO 8601 pattern
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$"
    return bool(re.match(pattern, timestamp))


class TestDatasourceSchema:
    """Tests for datasource schema validation."""

    def test_valid_datasource(self):
        """Test valid datasource passes validation."""
        data = {
            "releases": [
                {"version": "1.31.2-gke.1234", "releaseTimestamp": "2025-01-15T10:00:00Z"},
                {"version": "1.30.5-gke.100"},
            ]
        }
        errors = validate_datasource_schema(data)
        assert errors == []

    def test_empty_releases(self):
        """Test empty releases list is valid."""
        data = {"releases": []}
        errors = validate_datasource_schema(data)
        assert errors == []

    def test_missing_releases_key(self):
        """Test missing releases key fails validation."""
        data = {}
        errors = validate_datasource_schema(data)
        assert "Missing 'releases' key" in errors

    def test_releases_not_list(self):
        """Test releases as non-list fails validation."""
        data = {"releases": "not a list"}
        errors = validate_datasource_schema(data)
        assert "'releases' must be a list" in errors

    def test_release_missing_version(self):
        """Test release without version fails validation."""
        data = {"releases": [{"releaseTimestamp": "2025-01-15T10:00:00Z"}]}
        errors = validate_datasource_schema(data)
        assert any("missing 'version'" in e for e in errors)

    def test_release_empty_version(self):
        """Test release with empty version fails validation."""
        data = {"releases": [{"version": ""}]}
        errors = validate_datasource_schema(data)
        assert any("must not be empty" in e for e in errors)

    def test_invalid_timestamp_format(self):
        """Test invalid timestamp format fails validation."""
        data = {"releases": [{"version": "1.31.2-gke.1234", "releaseTimestamp": "invalid"}]}
        errors = validate_datasource_schema(data)
        assert any("ISO 8601" in e for e in errors)

    def test_valid_timestamp_formats(self):
        """Test various valid ISO 8601 formats."""
        timestamps = [
            "2025-01-15T10:00:00Z",
            "2025-01-15T10:00:00+00:00",
            "2025-01-15T10:00:00-05:00",
        ]
        for ts in timestamps:
            data = {"releases": [{"version": "1.0.0-gke.1", "releaseTimestamp": ts}]}
            errors = validate_datasource_schema(data)
            assert errors == [], f"Timestamp {ts} should be valid"


class TestGeneratedDatasourceFiles:
    """Tests for generated datasource files."""

    def test_all_datasource_files_have_valid_schema(self, datasources_dir):
        """Test all datasource files follow expected schema."""
        if datasources_dir is None:
            pytest.skip("Datasources directory not found")

        files = list(datasources_dir.glob("*.json"))
        assert len(files) > 0, "No datasource files found"

        for filepath in files:
            with open(filepath) as f:
                data = json.load(f)

            errors = validate_datasource_schema(data)
            assert errors == [], f"Schema validation errors in {filepath.name}: {errors}"

    def test_all_datasource_files_have_versions(self, datasources_dir):
        """Test all datasource files have at least some versions."""
        if datasources_dir is None:
            pytest.skip("Datasources directory not found")

        files = list(datasources_dir.glob("*.json"))
        assert len(files) > 0, "No datasource files found"

        for filepath in files:
            with open(filepath) as f:
                data = json.load(f)

            assert len(data.get("releases", [])) > 0, f"Expected at least one release in {filepath.name}"

"""
Tests for Yaegi Go compatibility datasource generator.
"""

import pytest

from sources.yaegi import (
    GO_DIRECTIVE_PATTERN,
    GoCompatRelease,
    extract_go_version,
)


class TestGoDirectivePattern:
    """Tests for the Go directive regex pattern."""

    @pytest.mark.parametrize(
        "content,expected",
        [
            ("go 1.21", "1.21"),
            ("go 1.22", "1.22"),
            ("go 1.23", "1.23"),
            ("module example\n\ngo 1.21\n", "1.21"),
            ("module example\n\ngo 1.22\n\nrequire (\n)", "1.22"),
        ],
    )
    def test_valid_go_directives(self, content: str, expected: str):
        """Test that valid go directives are matched."""
        match = GO_DIRECTIVE_PATTERN.search(content)
        assert match is not None
        assert match.group(1) == expected

    @pytest.mark.parametrize(
        "content",
        [
            "",
            "module example",
            "require golang 1.21",
            "// go 1.21",
        ],
    )
    def test_invalid_go_directives(self, content: str):
        """Test that invalid content does not match."""
        assert GO_DIRECTIVE_PATTERN.search(content) is None or extract_go_version(content) is None


class TestExtractGoVersion:
    """Tests for extract_go_version function."""

    def test_standard_gomod(self):
        """Test extraction from a standard go.mod."""
        content = """module github.com/traefik/yaegi

go 1.21
"""
        assert extract_go_version(content) == "1.21"

    def test_gomod_with_toolchain(self):
        """Test extraction when toolchain directive is present."""
        content = """module github.com/traefik/yaegi

go 1.22

toolchain go1.22.5
"""
        assert extract_go_version(content) == "1.22"

    def test_gomod_with_requires(self):
        """Test extraction from go.mod with require block."""
        content = """module github.com/example

go 1.23

require (
    github.com/some/dep v1.0.0
)
"""
        assert extract_go_version(content) == "1.23"

    def test_empty_content(self):
        """Test extraction from empty content."""
        assert extract_go_version("") is None

    def test_no_go_directive(self):
        """Test extraction when go directive is missing."""
        assert extract_go_version("module example\n") is None


class TestGoCompatRelease:
    """Tests for GoCompatRelease dataclass."""

    def test_to_dict_with_timestamp(self):
        """Test conversion to dict with timestamp."""
        release = GoCompatRelease(version="1.21", release_timestamp="2024-04-03T00:00:00Z")
        result = release.to_dict()
        assert result == {"version": "1.21", "releaseTimestamp": "2024-04-03T00:00:00Z"}

    def test_to_dict_without_timestamp(self):
        """Test conversion to dict without timestamp."""
        release = GoCompatRelease(version="1.22")
        result = release.to_dict()
        assert result == {"version": "1.22"}

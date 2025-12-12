"""
Pytest configuration and fixtures for datasource generator tests.
"""

from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--datasources-dir",
        action="store",
        default=None,
        help="Path to the datasources directory for validation tests",
    )


@pytest.fixture
def datasources_dir(request) -> Path | None:
    """Get the datasources directory from command line or default location."""
    cli_path = request.config.getoption("--datasources-dir")
    if cli_path:
        return Path(cli_path)

    # Default: repo-root/datasources
    # Path: tests/ -> datasource-generator-cli/ -> scripts/ -> .github/ -> repo-root/
    default_path = Path(__file__).parent.parent.parent.parent.parent / "datasources"
    if default_path.exists():
        return default_path

    return None

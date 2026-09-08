"""
Tests for datasource staleness detection.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from staleness import apply_first_seen, check_staleness, latest_release_age_days, warn_stale

NOW = datetime(2026, 9, 8, tzinfo=timezone.utc)


def _data(*timestamps: str | None) -> dict:
    releases = []
    for index, ts in enumerate(timestamps):
        release = {"version": f"1.35.{index}-gke.1000000"}
        if ts:
            release["releaseTimestamp"] = ts
        releases.append(release)
    return {"releases": releases}


class TestLatestReleaseAgeDays:
    def test_uses_the_newest_dated_release(self):
        data = _data("2026-07-01T00:00:00Z", "2026-09-01T00:00:00Z")
        assert latest_release_age_days(data, now=NOW) == pytest.approx(7.0)

    def test_ignores_undated_releases(self):
        data = _data(None, "2026-09-01T00:00:00Z", None)
        assert latest_release_age_days(data, now=NOW) == pytest.approx(7.0)

    def test_returns_none_when_nothing_is_dated(self):
        assert latest_release_age_days(_data(None, None), now=NOW) is None

    def test_returns_none_without_releases(self):
        assert latest_release_age_days({"releases": []}, now=NOW) is None

    def test_ignores_unparsable_timestamps(self):
        data = _data("not-a-date", "2026-09-01T00:00:00Z")
        assert latest_release_age_days(data, now=NOW) == pytest.approx(7.0)


class TestCheckStaleness:
    def test_fresh_source_is_not_stale(self):
        assert check_staleness("gke-regular", _data("2026-09-01T00:00:00Z"), 14, now=NOW) is None

    def test_source_at_the_limit_is_not_stale(self):
        data = _data((NOW - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        assert check_staleness("gke-regular", data, 14, now=NOW) is None

    def test_old_release_is_stale(self):
        stale = check_staleness("gke-regular", _data("2026-08-01T00:00:00Z"), 14, now=NOW)
        assert stale is not None
        assert stale.name == "gke-regular"
        assert stale.age_days == pytest.approx(38.0)
        assert "38.0 days old" in stale.detail

    def test_undated_source_is_stale(self):
        """A source we cannot date is not provably fresh, so it must be flagged."""
        stale = check_staleness("gke-regular", _data(None), 14, now=NOW)
        assert stale is not None
        assert stale.age_days is None
        assert "no release carries a date" in stale.detail


class TestApplyFirstSeen:
    def test_dates_undated_releases_with_today(self, tmp_path):
        data = _data(None, "2026-09-01T00:00:00Z")

        newly_seen = apply_first_seen(data, tmp_path / "missing.json", now=NOW)

        assert newly_seen == 1
        assert data["releases"][0]["releaseTimestamp"] == "2026-09-08T00:00:00Z"

    def test_leaves_existing_timestamps_untouched(self, tmp_path):
        data = _data("2026-09-01T00:00:00Z")

        newly_seen = apply_first_seen(data, tmp_path / "missing.json", now=NOW)

        assert newly_seen == 0
        assert data["releases"][0]["releaseTimestamp"] == "2026-09-01T00:00:00Z"

    def test_carries_previously_recorded_dates_forward(self, tmp_path):
        previous = tmp_path / "gke-rapid.json"
        previous.write_text(
            json.dumps({"releases": [{"version": "1.35.0-gke.1000000", "releaseTimestamp": "2026-08-20T00:00:00Z"}]})
        )
        data = {"releases": [{"version": "1.35.0-gke.1000000"}]}

        newly_seen = apply_first_seen(data, previous, now=NOW)

        assert newly_seen == 0
        assert data["releases"][0]["releaseTimestamp"] == "2026-08-20T00:00:00Z"

    def test_api_version_keeps_the_source_fresh(self, tmp_path):
        """The false positive this exists to prevent: a frozen feed plus a new API version."""
        data = {
            "releases": [
                {"version": "1.37.0-gke.2941000"},
                {"version": "1.37.0-gke.1173000", "releaseTimestamp": "2026-08-14T00:00:00Z"},
            ]
        }

        apply_first_seen(data, tmp_path / "missing.json", now=NOW)

        assert check_staleness("gke-rapid", data, 14, now=NOW) is None


class TestWarnStale:
    def test_emits_one_generic_annotation_in_ci(self, capsys, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        stale = check_staleness("gke-regular", _data("2026-08-01T00:00:00Z"), 14, now=NOW)

        warn_stale(stale)

        captured = capsys.readouterr()
        annotations = [line for line in captured.out.splitlines() if line.startswith("::")]
        assert len(annotations) == 1
        assert annotations[0].startswith("::warning title=Stale datasource::gke-regular is stale:")

    def test_no_annotation_outside_ci(self, capsys, monkeypatch):
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        stale = check_staleness("gke-regular", _data("2026-08-01T00:00:00Z"), 14, now=NOW)

        warn_stale(stale)

        captured = capsys.readouterr()
        assert "::" not in captured.out
        assert "WARNING" in captured.err

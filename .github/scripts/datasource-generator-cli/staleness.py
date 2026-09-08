"""
Datasource freshness: dating releases, and detecting stale sources.

A datasource is stale when its newest dated release is older than its
configured threshold. Because the generated file merges every input a source
has (for GKE: the authoritative Container API plus the release-notes feed), an
old newest release means the whole combination stopped producing fresh data,
not that a single input hiccuped.

The Container API publishes no release dates, so versions it contributes would
be invisible to that check. ``apply_first_seen`` dates them with the day we
first observed them, carrying previously recorded dates forward.
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(frozen=True)
class StaleSource:
    """A datasource whose newest release is older than its threshold."""

    name: str
    threshold_days: float
    age_days: Optional[float] = None

    @property
    def detail(self) -> str:
        if self.age_days is None:
            return f"no release carries a date (threshold {self.threshold_days:g} days)"
        return f"newest release is {self.age_days:.1f} days old (threshold {self.threshold_days:g} days)"


def apply_first_seen(data: dict, previous_path: Path, now: Optional[datetime] = None) -> int:
    """Date releases their source cannot date, and return how many are newly seen."""
    known = {}
    if previous_path.exists():
        with open(previous_path) as f:
            previous = json.load(f)
        known = {
            release["version"]: release["releaseTimestamp"]
            for release in previous.get("releases", [])
            if release.get("version") and release.get("releaseTimestamp")
        }

    stamp = (now or datetime.now(timezone.utc)).strftime(TIMESTAMP_FORMAT)
    newly_seen = 0
    for release in data.get("releases", []):
        if release.get("releaseTimestamp"):
            continue
        carried = known.get(release.get("version"))
        release["releaseTimestamp"] = carried or stamp
        if not carried:
            newly_seen += 1

    return newly_seen


def latest_release_age_days(data: dict, now: Optional[datetime] = None) -> Optional[float]:
    """Return the age in days of the newest dated release, or None if none is dated."""
    timestamps = []
    for release in data.get("releases", []):
        raw = release.get("releaseTimestamp")
        if not raw:
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        timestamps.append(parsed)

    if not timestamps:
        return None

    now = now or datetime.now(timezone.utc)
    return (now - max(timestamps)).total_seconds() / 86400


def check_staleness(
    name: str,
    data: dict,
    threshold_days: float,
    now: Optional[datetime] = None,
) -> Optional[StaleSource]:
    """Return a StaleSource when the datasource has no recent release, else None."""
    age_days = latest_release_age_days(data, now=now)
    if age_days is not None and age_days <= threshold_days:
        return None
    return StaleSource(name=name, threshold_days=threshold_days, age_days=age_days)


def warn_stale(stale: StaleSource) -> None:
    """Emit the single generic staleness warning for a datasource."""
    message = f"{stale.name} is stale: {stale.detail}. Its upstream release data may no longer be updated."
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title=Stale datasource::{message}")
    print(f"  WARNING: {message}", file=sys.stderr)

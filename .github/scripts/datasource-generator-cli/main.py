#!/usr/bin/env python3
"""
Datasource Generator CLI

A framework for generating Renovate custom datasources from various sources.
"""

import argparse
import json
import os
import sys
from functools import partial
from pathlib import Path

from sources.gke import GKEChannel, fetch_gke_versions
from sources.yaegi import fetch_yaegi_go_compat
from staleness import StaleSource, apply_first_seen, check_staleness, warn_stale

# Every GKE channel ships often enough that a fortnight without a release means the source dried up.
GKE_STALENESS_THRESHOLD_DAYS = 14

# Registry of available datasource generators
DATASOURCE_REGISTRY = {
    "gke-rapid": {
        "generator": partial(fetch_gke_versions, GKEChannel.RAPID),
        "output_file": "gke-rapid.json",
        "description": "GKE Rapid channel versions",
        "accepts_gke_options": True,
        "staleness_threshold_days": GKE_STALENESS_THRESHOLD_DAYS,
    },
    "gke-regular": {
        "generator": partial(fetch_gke_versions, GKEChannel.REGULAR),
        "output_file": "gke-regular.json",
        "description": "GKE Regular channel versions",
        "accepts_gke_options": True,
        "staleness_threshold_days": GKE_STALENESS_THRESHOLD_DAYS,
    },
    "gke-stable": {
        "generator": partial(fetch_gke_versions, GKEChannel.STABLE),
        "output_file": "gke-stable.json",
        "description": "GKE Stable channel versions",
        "accepts_gke_options": True,
        "staleness_threshold_days": GKE_STALENESS_THRESHOLD_DAYS,
    },
    "gke-extended": {
        "generator": partial(fetch_gke_versions, GKEChannel.EXTENDED),
        "output_file": "gke-extended.json",
        "description": "GKE Extended channel versions",
        "accepts_gke_options": True,
        "staleness_threshold_days": GKE_STALENESS_THRESHOLD_DAYS,
    },
    "yaegi-go-compat": {
        "generator": fetch_yaegi_go_compat,
        "output_file": "yaegi-go-compat.json",
        "description": "Yaegi supported Go version (from go.mod directive)",
    },
}


def generate_datasource(
    name: str,
    output_dir: Path,
    gke_options: dict | None = None,
) -> StaleSource | None:
    """Generate a single datasource, write it to file, and report its staleness."""
    if name not in DATASOURCE_REGISTRY:
        raise ValueError(f"Unknown datasource: {name}. Available: {list(DATASOURCE_REGISTRY.keys())}")

    config = DATASOURCE_REGISTRY[name]
    generator = config["generator"]
    output_file = output_dir / config["output_file"]

    kwargs = gke_options or {} if config.get("accepts_gke_options") else {}

    print(f"Generating {name} datasource...")
    data = generator(**kwargs)

    # Read the previous output before overwriting it, to keep first-seen dates stable.
    newly_seen = apply_first_seen(data, output_file)

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Written to {output_file}")
    print(f"  Total releases: {len(data.get('releases', []))}")
    if newly_seen:
        print(f"  {newly_seen} version(s) carry no upstream release date; dated as first seen today")

    threshold_days = config.get("staleness_threshold_days")
    if threshold_days is None:
        return None

    stale = check_staleness(name, data, threshold_days)
    if stale:
        warn_stale(stale)
    return stale


def generate_all(output_dir: Path, gke_options: dict | None = None) -> list[StaleSource]:
    """Generate all registered datasources and return the stale ones."""
    stale_sources = []
    for name in DATASOURCE_REGISTRY:
        try:
            stale = generate_datasource(name, output_dir, gke_options)
            if stale:
                stale_sources.append(stale)
        except Exception as e:
            print(f"Error generating {name}: {e}", file=sys.stderr)
            raise
    return stale_sources


def write_stale_report(path: Path, stale_sources: list[StaleSource]) -> None:
    """Write the staleness result so a later CI step can act on it after committing."""
    report = {
        "stale": [
            {
                "name": s.name,
                "ageDays": s.age_days,
                "thresholdDays": s.threshold_days,
                "detail": s.detail,
            }
            for s in sorted(stale_sources, key=lambda s: s.name)
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Stale report written to {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Renovate custom datasources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available datasources:
  gke-rapid      GKE Rapid channel versions
  gke-regular    GKE Regular channel versions
  gke-stable     GKE Stable channel versions
  gke-extended   GKE Extended channel versions

Examples:
  %(prog)s --all                    Generate all datasources
  %(prog)s --datasource gke-rapid   Generate only GKE Rapid datasource
  %(prog)s --list                   List available datasources
""",
    )

    parser.add_argument(
        "--datasource",
        "-d",
        choices=list(DATASOURCE_REGISTRY.keys()),
        help="Generate a specific datasource",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Generate all datasources",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("datasources"),
        help="Output directory for generated files (default: datasources)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available datasources",
    )
    parser.add_argument(
        "--gcp-project",
        default=os.environ.get("GKE_DATASOURCE_GCP_PROJECT"),
        help="GCP project used to query the authoritative GKE Container API",
    )
    parser.add_argument(
        "--gcp-location",
        default=os.environ.get("GKE_DATASOURCE_GCP_LOCATION"),
        help="GCP location (region) used to query the authoritative GKE Container API",
    )
    parser.add_argument(
        "--stale-report",
        type=Path,
        metavar="PATH",
        help="Write the stale datasource report as JSON to this path",
    )

    args = parser.parse_args()

    if args.list:
        print("Available datasources:")
        for name, config in DATASOURCE_REGISTRY.items():
            print(f"  {name}: {config['description']}")
        return 0

    if bool(args.gcp_project) != bool(args.gcp_location):
        print("--gcp-project and --gcp-location must be provided together", file=sys.stderr)
        return 1

    gke_options = {
        "project": args.gcp_project,
        "location": args.gcp_location,
    }

    if args.all:
        try:
            stale_sources = generate_all(args.output_dir, gke_options)
        except Exception as e:
            print(f"Failed to generate datasources: {e}", file=sys.stderr)
            return 1

        print(f"\nGenerated {len(DATASOURCE_REGISTRY)} datasource(s)")
        if args.stale_report:
            write_stale_report(args.stale_report, stale_sources)
        return 0

    if args.datasource:
        try:
            stale = generate_datasource(args.datasource, args.output_dir, gke_options)
        except Exception as e:
            print(f"Failed to generate {args.datasource}: {e}", file=sys.stderr)
            return 1

        if args.stale_report:
            write_stale_report(args.stale_report, [stale] if stale else [])
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

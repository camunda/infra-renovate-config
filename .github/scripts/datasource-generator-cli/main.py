#!/usr/bin/env python3
"""
Datasource Generator CLI

A framework for generating Renovate custom datasources from various sources.
"""

import argparse
import json
import sys
from functools import partial
from pathlib import Path

from sources.gke import GKEChannel, fetch_gke_versions

# Registry of available datasource generators
DATASOURCE_REGISTRY = {
    "gke-rapid": {
        "generator": partial(fetch_gke_versions, GKEChannel.RAPID),
        "output_file": "gke-rapid.json",
        "description": "GKE Rapid channel versions",
    },
    "gke-regular": {
        "generator": partial(fetch_gke_versions, GKEChannel.REGULAR),
        "output_file": "gke-regular.json",
        "description": "GKE Regular channel versions",
    },
    "gke-stable": {
        "generator": partial(fetch_gke_versions, GKEChannel.STABLE),
        "output_file": "gke-stable.json",
        "description": "GKE Stable channel versions",
    },
    "gke-extended": {
        "generator": partial(fetch_gke_versions, GKEChannel.EXTENDED),
        "output_file": "gke-extended.json",
        "description": "GKE Extended channel versions",
    },
}


def generate_datasource(name: str, output_dir: Path) -> Path:
    """Generate a single datasource and write to file."""
    if name not in DATASOURCE_REGISTRY:
        raise ValueError(f"Unknown datasource: {name}. Available: {list(DATASOURCE_REGISTRY.keys())}")

    config = DATASOURCE_REGISTRY[name]
    generator = config["generator"]
    output_file = output_dir / config["output_file"]

    print(f"Generating {name} datasource...")
    data = generator()

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Written to {output_file}")
    print(f"  Total releases: {len(data.get('releases', []))}")

    return output_file


def generate_all(output_dir: Path) -> list[Path]:
    """Generate all registered datasources."""
    outputs = []
    for name in DATASOURCE_REGISTRY:
        try:
            output = generate_datasource(name, output_dir)
            outputs.append(output)
        except Exception as e:
            print(f"Error generating {name}: {e}", file=sys.stderr)
            raise
    return outputs


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

    args = parser.parse_args()

    if args.list:
        print("Available datasources:")
        for name, config in DATASOURCE_REGISTRY.items():
            print(f"  {name}: {config['description']}")
        return 0

    if args.all:
        try:
            outputs = generate_all(args.output_dir)
            print(f"\nGenerated {len(outputs)} datasource(s)")
            return 0
        except Exception as e:
            print(f"Failed to generate datasources: {e}", file=sys.stderr)
            return 1

    if args.datasource:
        try:
            generate_datasource(args.datasource, args.output_dir)
            return 0
        except Exception as e:
            print(f"Failed to generate {args.datasource}: {e}", file=sys.stderr)
            return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

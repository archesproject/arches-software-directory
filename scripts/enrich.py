#!/usr/bin/env python3
"""
Reads all manifest YAML files from packages/ and enriches them with live data
from the PyPI JSON API and the GitHub API, then writes a combined JSON file
that the static site generator consumes.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
import yaml


PYPI_API = "https://pypi.org/pypi/{name}/json"
GITHUB_API = "https://api.github.com/repos/{owner}/{repo}"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

REQUEST_TIMEOUT = 15
RATE_LIMIT_PAUSE = 0.5  # seconds between GitHub requests


def github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_pypi_data(pypi_name):
    """Returns a dict of live PyPI metadata, or empty dict on failure."""
    try:
        response = requests.get(
            PYPI_API.format(name=pypi_name), timeout=REQUEST_TIMEOUT
        )
        if response.status_code != 200:
            return {}

        data = response.json()
        info = data.get("info", {})
        releases = data.get("releases", {})

        # Count total downloads across all versions from the simple download_url
        # (PyPI JSON doesn't include download counts; we note the latest version instead)
        return {
            "pypi_version": info.get("version"),
            "pypi_summary": info.get("summary"),
            "pypi_url": info.get("package_url"),
            "requires_python": info.get("requires_python"),
        }
    except Exception:
        return {}


def extract_github_owner_repo(repository_url):
    """Parses 'https://github.com/owner/repo' into (owner, repo), or None."""
    if not repository_url or "github.com" not in repository_url:
        return None
    parts = repository_url.rstrip("/").split("/")
    if len(parts) >= 5:
        return parts[-2], parts[-1]
    return None


def fetch_github_data(repository_url):
    """Returns a dict of live GitHub metadata, or empty dict on failure."""
    parsed = extract_github_owner_repo(repository_url)
    if not parsed:
        return {}

    owner, repo = parsed
    try:
        time.sleep(RATE_LIMIT_PAUSE)
        response = requests.get(
            GITHUB_API.format(owner=owner, repo=repo),
            headers=github_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            return {}

        data = response.json()
        return {
            "github_stars": data.get("stargazers_count"),
            "github_forks": data.get("forks_count"),
            "github_open_issues": data.get("open_issues_count"),
            "github_last_push": data.get("pushed_at"),
            "github_default_branch": data.get("default_branch"),
            "github_topics": data.get("topics", []),
        }
    except Exception:
        return {}


def load_manifests(packages_dir):
    packages_path = Path(packages_dir)
    manifests = []
    for yaml_file in sorted(packages_path.glob("*.yaml")):
        with open(yaml_file) as f:
            manifest = yaml.safe_load(f)
        manifest["_source_file"] = yaml_file.name
        manifests.append(manifest)
    return manifests


def enrich(manifests):
    enriched = []
    for manifest in manifests:
        package = dict(manifest)

        pypi_name = manifest.get("pypi")
        if pypi_name:
            print(f"  Fetching PyPI data for {pypi_name}...")
            package["_pypi"] = fetch_pypi_data(pypi_name)

        repo_url = manifest.get("repository")
        if repo_url:
            print(f"  Fetching GitHub data for {repo_url}...")
            package["_github"] = fetch_github_data(repo_url)

        enriched.append(package)

    return enriched


def summarize_coverage(enriched):
    """Returns {source: (successes, attempts)} for the live data lookups.

    A failed lookup leaves an empty dict behind, so an empty value means the API
    call did not produce anything usable.
    """
    coverage = {}
    for source in ("_pypi", "_github"):
        attempts = [p for p in enriched if source in p]
        successes = [p for p in attempts if p[source]]
        coverage[source.lstrip("_")] = (len(successes), len(attempts))
    return coverage


def main():
    parser = argparse.ArgumentParser(description="Enrich manifests with live API data")
    parser.add_argument(
        "--packages-dir", default="packages", help="Path to packages/ directory"
    )
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument(
        "--fail-on-total-failure",
        action="store_true",
        help=(
            "Exit non-zero if a data source was attempted but returned nothing at all. "
            "Used by the scheduled rebuild so a rate-limited run leaves the previous "
            "deploy in place instead of publishing a site with blank stars and versions."
        ),
    )
    args = parser.parse_args()

    print(f"Loading manifests from {args.packages_dir}/...")
    manifests = load_manifests(args.packages_dir)
    print(f"Found {len(manifests)} manifests.")

    print("Enriching with live data...")
    enriched = enrich(manifests)

    coverage = summarize_coverage(enriched)
    print("Live data coverage:")
    for source, (successes, attempts) in coverage.items():
        print(f"  {source}: {successes}/{attempts} lookups returned data")

    collapsed = [
        source
        for source, (successes, attempts) in coverage.items()
        if attempts and not successes
    ]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(enriched, f, indent=2, default=str)

    print(f"Wrote {len(enriched)} enriched packages to {output_path}")

    if collapsed:
        message = (
            f"Every {', '.join(collapsed)} lookup failed — likely rate limiting or an "
            f"API outage, not a manifest problem."
        )
        if args.fail_on_total_failure:
            print(f"ERROR: {message}", file=sys.stderr)
            return 1
        print(f"WARNING: {message}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

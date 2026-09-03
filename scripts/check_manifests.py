#!/usr/bin/env python3
"""
Checks that the URLs and PyPI names in manifest files still resolve.

Results are split into two categories, because "the checker was refused" is not
the same finding as "the link is dead":

  failure       the reference is genuinely broken (404/410, PyPI name not found)
  inconclusive  the checker was blocked or throttled (403/405/429/5xx, timeouts)

Only failures set a non-zero exit status. Inconclusive results are reported so a
maintainer can eyeball them, but they never red-build a pull request, because the
cause is usually a bot-management rule on someone else's site rather than
anything wrong with the manifest.
"""

import argparse
import os
import sys
import time
from pathlib import Path

import requests
import yaml


# A descriptive User-Agent gets past most default bot rules; the bare
# "python-requests/x.y" default is a well-known signature and is frequently
# challenged, which is what made these checks flaky in the first place.
USER_AGENT = (
    "arches-software-directory-ci/1.0 "
    "(+https://github.com/archesproject/arches-software-directory)"
)

REQUEST_TIMEOUT = 20
RETRY_DELAYS = (1, 3, 6)

# Refusals and throttling: the reference may be perfectly fine.
INCONCLUSIVE_STATUSES = {401, 402, 403, 405, 406, 429}

# Definitive "this is not there".
DEAD_STATUSES = {404, 410}

OK = "ok"
FAILURE = "failure"
INCONCLUSIVE = "inconclusive"


def build_session():
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    return session


def check_url(session, url):
    """Returns (verdict, detail). Tries HEAD first, then GET.

    Plenty of hosts either do not implement HEAD or treat it as suspicious, so a
    HEAD refusal is never taken as the final answer.
    """
    last_detail = "no response"

    for attempt, delay in enumerate((0,) + RETRY_DELAYS):
        if delay:
            time.sleep(delay)

        for method in ("HEAD", "GET"):
            try:
                response = session.request(
                    method,
                    url,
                    allow_redirects=True,
                    timeout=REQUEST_TIMEOUT,
                    stream=(method == "GET"),
                )
            except requests.RequestException as exc:
                last_detail = f"{method} raised {type(exc).__name__}"
                continue

            status = response.status_code
            if method == "GET":
                response.close()

            if status < 400:
                return OK, f"{method} {status}"
            if status in DEAD_STATUSES:
                return FAILURE, f"{method} returned {status}"
            last_detail = f"{method} returned {status}"

        # Transient-looking; fall through to the next retry if any remain.

    return INCONCLUSIVE, last_detail


def check_pypi(session, pypi_name):
    """A 404 means the name is not registered; anything else is inconclusive."""
    url = f"https://pypi.org/pypi/{pypi_name}/json"

    for delay in (0,) + RETRY_DELAYS:
        if delay:
            time.sleep(delay)
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            detail = f"request raised {type(exc).__name__}"
            continue

        if response.status_code == 404:
            return FAILURE, "not registered on PyPI"
        if response.status_code < 400:
            return OK, "found on PyPI"
        detail = f"PyPI returned {response.status_code}"

    return INCONCLUSIVE, detail


def load_manifest(path):
    with open(path) as handle:
        return yaml.safe_load(handle)


def collect_results(session, paths):
    """Returns a list of (package_name, check_label, verdict, detail, target)."""
    results = []

    for path in paths:
        if not os.path.exists(path):
            # A manifest removed or renamed in this PR: nothing left to check.
            continue

        manifest = load_manifest(path)
        if not isinstance(manifest, dict):
            # Schema validation reports malformed manifests; do not double-report.
            continue

        package_name = manifest.get("name") or path

        for field in ("repository", "docs"):
            target = manifest.get(field)
            if target:
                verdict, detail = check_url(session, target)
                results.append((package_name, field, verdict, detail, target))

        pypi_name = manifest.get("pypi")
        if pypi_name:
            verdict, detail = check_pypi(session, pypi_name)
            results.append((package_name, "pypi", verdict, detail, pypi_name))

    return results


def write_step_summary(results, checked_count):
    """Renders a table into the GitHub Actions job summary, when running there."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    failures = [r for r in results if r[2] == FAILURE]
    inconclusive = [r for r in results if r[2] == INCONCLUSIVE]

    lines = [
        "## Manifest reference check",
        "",
        f"Checked **{checked_count}** manifest(s): "
        f"{len(failures)} failure(s), {len(inconclusive)} inconclusive, "
        f"{len(results) - len(failures) - len(inconclusive)} ok.",
        "",
    ]

    for heading, rows in (("Failures", failures), ("Inconclusive", inconclusive)):
        if not rows:
            continue
        lines += [
            f"### {heading}",
            "",
            "| package | check | target | detail |",
            "| --- | --- | --- | --- |",
        ]
        for package_name, label, _verdict, detail, target in rows:
            lines.append(f"| `{package_name}` | {label} | {target} | {detail} |")
        lines.append("")

    if not failures and not inconclusive:
        lines += ["Every reference resolved.", ""]

    with open(summary_path, "a") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Check manifest repository/docs URLs and PyPI names"
    )
    parser.add_argument(
        "--packages-dir",
        default="packages",
        help="Directory holding manifest YAML files",
    )
    parser.add_argument(
        "--all", action="store_true", help="Check every manifest in --packages-dir"
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read newline-separated manifest paths from stdin (blank lines ignored)",
    )
    parser.add_argument(
        "files", nargs="*", help="Specific manifest paths to check (ignored with --all)"
    )
    args = parser.parse_args()

    if args.all:
        paths = sorted(str(p) for p in Path(args.packages_dir).glob("*.yaml"))
    elif args.stdin:
        # Reading the list rather than expanding it in the shell keeps paths with
        # spaces intact and avoids depending on bash 4 built-ins.
        paths = [line.strip() for line in sys.stdin if line.strip()]
    else:
        paths = [f.strip() for f in args.files if f.strip()]

    if not paths:
        print("No manifests to check.")
        return 0

    session = build_session()
    results = collect_results(session, paths)

    failures = [r for r in results if r[2] == FAILURE]
    inconclusive = [r for r in results if r[2] == INCONCLUSIVE]

    for package_name, label, verdict, detail, target in results:
        if verdict == OK:
            print(f"  ok           {package_name} {label}: {target}")

    if inconclusive:
        print("\nInconclusive (checker refused or throttled; not treated as an error):")
        for package_name, label, _v, detail, target in inconclusive:
            print(f"  - {package_name} {label}: {target} ({detail})")

    if failures:
        print("\nFailures:")
        for package_name, label, _v, detail, target in failures:
            print(f"  - {package_name} {label}: {target} ({detail})")

    write_step_summary(results, len(paths))

    print(
        f"\nChecked {len(paths)} manifest(s): "
        f"{len(failures)} failure(s), {len(inconclusive)} inconclusive."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

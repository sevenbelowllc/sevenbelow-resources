#!/usr/bin/env python3
"""scrub-check.py — verify a security-review/ output dir does not contain
secrets, tokens, customer names, or other publish-blocking content.

Usage:
  scrub-check.py <review-dir> [--config <patterns-file>]

Default deny-pattern set covers:
  - JWT-shaped strings (eyJ...)
  - common API-key prefixes (sk_live_, sk_test_, pk_*, ghp_, ghs_, gho_,
    AKIA, ASIA, AIza, xox[abps]-)
  - private-key headers (BEGIN PRIVATE KEY, BEGIN RSA PRIVATE KEY, etc.)
  - .pem / .key / .p12 / .pfx / .jks file references
  - PLACEHOLDER_* literals are PERMITTED (workspace-friendly convention)

Customer / hostname / Jira-key denial is operator-supplied via --config FILE
(one regex per line; lines starting with `#` are comments). Keeps this script
generic.

Exit codes:
  0 = clean
  1 = matches found (review NOT safe to publish)
  2 = misuse / dir not found
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


# Default deny patterns (extended regex flavor; one per category).
DEFAULT_PATTERNS: list[tuple[str, str]] = [
    ("JWT (3-segment eyJ...)", r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("Stripe secret key", r"sk_(live|test)_[A-Za-z0-9]{16,}"),
    ("Stripe publishable key", r"pk_(live|test)_[A-Za-z0-9]{16,}"),
    ("GitHub personal token", r"ghp_[A-Za-z0-9]{20,}"),
    ("GitHub server token", r"ghs_[A-Za-z0-9]{20,}"),
    ("GitHub OAuth token", r"gho_[A-Za-z0-9]{20,}"),
    ("AWS access key (AKIA)", r"AKIA[0-9A-Z]{16}"),
    ("AWS access key (ASIA)", r"ASIA[0-9A-Z]{16}"),
    ("Google API key (AIza)", r"AIza[0-9A-Za-z_-]{20,}"),
    ("Slack token", r"xox[abps]-[A-Za-z0-9-]{8,}"),
    ("Private key header", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

PRIVATE_KEY_FILE_REF = (
    "Private-key file reference",
    r"\.(pem|key|p12|pfx|jks)\b",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pre-publish secret scan for review output.")
    p.add_argument("review_dir", help="Directory to scan recursively.")
    p.add_argument(
        "--config",
        help="Path to operator-curated patterns file (one regex per line, # for comments).",
    )
    return p.parse_args()


def load_custom_patterns(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append((f"custom: {line}", line))
    return out


def scan_dir(
    root: Path, patterns: list[tuple[str, str]]
) -> list[tuple[str, Path, int, str]]:
    """Return list of (label, file, lineno, line_text) for each match."""
    matches: list[tuple[str, Path, int, str]] = []
    compiled = [(label, re.compile(pat)) for label, pat in patterns]
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for label, regex in compiled:
                if regex.search(line):
                    matches.append((label, path, lineno, line.rstrip()))
    return matches


def main() -> int:
    args = parse_args()
    root = Path(args.review_dir)
    if not root.is_dir():
        print(f"directory not found: {root}", file=sys.stderr)
        return 2

    patterns = list(DEFAULT_PATTERNS) + [PRIVATE_KEY_FILE_REF]

    if args.config:
        cfg = Path(args.config)
        if not cfg.is_file():
            print(f"config not found: {cfg}", file=sys.stderr)
            return 2
        patterns.extend(load_custom_patterns(cfg))

    print(f"== scrub-check on {root} ==")
    print(f"patterns loaded: {len(patterns)}")

    matches = scan_dir(root, patterns)

    if not matches:
        print()
        print("PASS: no patterns matched. Review safe to share at this layer.")
        print("Note: this script does not detect customer names, hostnames, or PII —")
        print("      supply --config with operator-curated patterns for that coverage.")
        return 0

    print()
    print("MATCHES:")
    for label, path, lineno, line in matches:
        # Truncate long lines for readability
        snippet = line if len(line) <= 120 else line[:117] + "..."
        print(f"  [{label}] {path}:{lineno}: {snippet}")

    print()
    print(f"FAIL: {root} contains {len(matches)} match(es). Do not publish.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

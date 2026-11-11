"""Offline-safe unit-testable helper for immutable material snapshot tags.

The helper is intentionally not invoked by the test suite against a real remote.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import re
import subprocess
import uuid
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

REPOSITORY = "otromas1234/material-asignaturas"
BRANCH = "main"
MAX_ATTEMPTS = 5


class TagError(RuntimeError):
    pass


def _validate_subject_date(slug: str, yyyymmdd: str) -> None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise TagError("invalid subject slug")
    if not re.fullmatch(r"\d{8}", yyyymmdd):
        raise TagError("invalid date")
    try:
        if datetime.strptime(yyyymmdd, "%Y%m%d").strftime("%Y%m%d") != yyyymmdd:
            raise ValueError
    except ValueError as error:
        raise TagError("date is not a valid calendar date") from error


def _git(repo: Path, args: tuple[str, ...], runner: Callable) -> str:
    result = runner(["git", "-C", str(repo), *args], text=True,
                    capture_output=True, check=False)
    if result.returncode:
        raise TagError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _preflight(repo: Path, *, runner: Callable) -> None:
    origin = _git(repo, ("remote", "get-url", "origin"), runner)
    parsed = urlparse(origin if "://" in origin else "ssh://" + origin.replace(":", "/", 1))
    if parsed.hostname != "github.com" or parsed.path.removesuffix(".git").strip("/") != REPOSITORY:
        raise TagError("origin is not the authorized repository")
    if _git(repo, ("branch", "--show-current"), runner) != BRANCH:
        raise TagError("checkout is not the authorized branch")
    _git(repo, ("fetch", "--no-tags", "origin", BRANCH), runner)


def _tag_absence(repo: Path, tag: str, *, runner: Callable) -> bool:
    local = runner(["git", "-C", str(repo), "show-ref", "--verify", "--quiet",
                    f"refs/tags/{tag}"], text=True, capture_output=True, check=False)
    if local.returncode == 0:
        return False
    if local.returncode != 1:
        raise TagError("could not verify local tag absence")
    remote = runner(["git", "-C", str(repo), "ls-remote", "--exit-code", "--refs",
                     "origin", f"refs/tags/{tag}"], text=True, capture_output=True, check=False)
    if remote.returncode == 2:
        return True
    if remote.returncode == 0:
        return False
    raise TagError("could not verify remote tag absence")


def preflight_tag(repo: Path, slug: str, yyyymmdd: str, *,
                  runner: Callable = subprocess.run,
                  suffix_factory: Callable[[], str] = lambda: uuid.uuid4().hex[:8],
                  max_attempts: int = MAX_ATTEMPTS) -> str:
    """Choose an unused tag name before material commit; this does not reserve it."""
    _validate_subject_date(slug, yyyymmdd)
    if not 1 <= max_attempts <= MAX_ATTEMPTS:
        raise TagError("attempt limit must be between 1 and 5")
    _preflight(repo, runner=runner)
    for _ in range(max_attempts):
        suffix = suffix_factory()
        if not re.fullmatch(r"[0-9a-f]{4,16}", suffix):
            raise TagError("suffix factory returned an invalid identifier")
        tag = f"plan/{slug}/{yyyymmdd}-{suffix}"
        if _tag_absence(repo, tag, runner=runner):
            return tag
    raise TagError("no unique tag name available within bounded attempts")


def publish_tag(repo: Path, tag: str, commit_sha: str,
                *, runner: Callable = subprocess.run) -> str:
    """Publish a preflight-selected tag on exact SHA; recheck absence to fail closed."""
    match = re.fullmatch(r"plan/([a-z0-9]+(?:-[a-z0-9]+)*)/(\d{8})-([0-9a-f]{4,16})", tag)
    if not match:
        raise TagError("invalid snapshot tag format")
    _validate_subject_date(match.group(1), match.group(2))
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise TagError("commit SHA must be a full lowercase SHA-1")
    _preflight(repo, runner=runner)
    resolved = _git(repo, ("rev-parse", "--verify", f"{commit_sha}^{{commit}}"), runner)
    if resolved != commit_sha:
        raise TagError("requested SHA does not resolve exactly")
    ancestry = runner(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                      commit_sha, f"refs/remotes/origin/{BRANCH}"], text=True,
                     capture_output=True, check=False)
    if ancestry.returncode == 1:
        raise TagError("requested SHA is not reachable from the authorized branch")
    if ancestry.returncode != 0:
        raise TagError("could not verify requested SHA reachability")
    if not _tag_absence(repo, tag, runner=runner):
        raise TagError("preflight tag now exists; possible race, refusing to move it")
    _git(repo, ("tag", tag, commit_sha), runner)
    _git(repo, ("push", "origin", f"refs/tags/{tag}"), runner)
    verified = _git(repo, ("ls-remote", "--refs", "origin", f"refs/tags/{tag}"), runner)
    if verified != f"{commit_sha}\trefs/tags/{tag}":
        raise TagError("remote tag does not point to the exact requested SHA")
    return tag


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preflight and publish immutable material snapshot tags.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight", help="select a free tag name before material commit")
    preflight.add_argument("--repo", required=True, type=Path)
    preflight.add_argument("--slug", required=True)
    preflight.add_argument("--date", required=True, dest="yyyymmdd")
    publish = subparsers.add_parser("publish", help="publish a preflight-selected tag on the final commit SHA")
    publish.add_argument("--repo", required=True, type=Path)
    publish.add_argument("--tag", required=True)
    publish.add_argument("--sha", required=True, dest="commit_sha")
    args = parser.parse_args(argv)
    try:
        tag = (preflight_tag(args.repo, args.slug, args.yyyymmdd) if args.command == "preflight"
               else publish_tag(args.repo, args.tag, args.commit_sha))
    except (TagError, OSError) as error:
        parser.exit(1, f"tag snapshot failed: {error}\n")
    print(f"tag={tag}" + (f" sha={args.commit_sha}" if args.command == "publish" else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

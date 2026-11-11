import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPT_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
from tag_snapshot import BRANCH, MAX_ATTEMPTS, TagError, preflight_tag, publish_tag

SHA = "a" * 40


class FakeGit:
    def __init__(self, *, origin="https://github.com/otromas1234/material-asignaturas.git",
                 branch=BRANCH, resolved=SHA, existing=(), remote_sha=None,
                 ancestry_code=0, show_ref_code=None, push_race=False,
                 fetch_code=0):
        self.origin, self.branch, self.resolved = origin, branch, resolved
        self.local_tags, self.remote_tags = set(existing), set(existing)
        self.remote_sha = remote_sha or SHA
        self.ancestry_code = ancestry_code
        self.show_ref_code = show_ref_code
        self.push_race = push_race
        self.fetch_code = fetch_code
        self.calls = []

    def __call__(self, argv, **kwargs):
        args = argv[3:]
        self.calls.append(args)
        out, code = "", 0
        if args[:2] == ["remote", "get-url"]:
            out = self.origin
        elif args == ["branch", "--show-current"]:
            out = self.branch
        elif args == ["fetch", "--no-tags", "origin", BRANCH]:
            code = self.fetch_code
        elif args[:2] == ["rev-parse", "--verify"]:
            out = self.resolved
        elif args[:2] == ["merge-base", "--is-ancestor"]:
            if args[-1] != f"refs/remotes/origin/{BRANCH}":
                code = 128
            else:
                code = self.ancestry_code
        elif args[:2] == ["show-ref", "--verify"]:
            code = (self.show_ref_code if self.show_ref_code is not None else
                    0 if args[-1].removeprefix("refs/tags/") in self.local_tags else 1)
        elif args[:2] == ["ls-remote", "--exit-code"]:
            tag = args[-1].removeprefix("refs/tags/")
            code = 0 if tag in self.remote_tags else 2
            if code == 0:
                out = f"{self.remote_sha}\trefs/tags/{tag}"
        elif args[0] == "tag":
            self.local_tags.add(args[1])
        elif args[0] == "push":
            tag = args[-1].removeprefix("refs/tags/")
            if self.push_race:
                self.remote_tags.add(tag)
                code = 1
            elif tag in self.remote_tags:
                code = 1
            else:
                self.remote_tags.add(tag)
        elif args[:2] == ["ls-remote", "--refs"]:
            tag = args[-1].removeprefix("refs/tags/")
            code = 0 if tag in self.remote_tags else 2
            if code == 0:
                out = f"{self.remote_sha}\trefs/tags/{tag}"
        return SimpleNamespace(returncode=code, stdout=out, stderr="simulated failure")


class TagHelperTests(unittest.TestCase):
    def run_preflight(self, fake, suffixes, limit=MAX_ATTEMPTS, date="20261030"):
        iterator = iter(suffixes)
        return preflight_tag(Path("/fake/repo"), "historia", date,
                           runner=fake, suffix_factory=lambda: next(iterator),
                           max_attempts=limit)

    def run_publish(self, fake, tag="plan/historia/20261030-abcd", sha=SHA):
        return publish_tag(Path("/fake/repo"), tag, sha, runner=fake)

    def test_rejects_wrong_repository_branch_and_unresolved_sha_before_writes(self):
        for fake in (FakeGit(origin="https://github.com/other/repo"),
                     FakeGit(origin="https://evilgithub.com/otromas1234/material-asignaturas"),
                     FakeGit(branch="development")):
            with self.subTest(fake=fake.origin, branch=fake.branch):
                with self.assertRaises(TagError):
                    self.run_preflight(fake, ["1111"])
                self.assertFalse(any(call[0] in {"tag", "push"} for call in fake.calls))

    def test_publish_rejects_wrong_sha_or_unreachable_commit(self):
        for fake in (FakeGit(resolved="b" * 40), FakeGit(ancestry_code=1)):
            with self.subTest(resolved=fake.resolved, ancestry=fake.ancestry_code):
                with self.assertRaises(TagError):
                    self.run_publish(fake)
                self.assertFalse(any(call[0] in {"tag", "push"} for call in fake.calls))

    def test_retries_collisions_without_moving_existing_tag(self):
        old = "plan/historia/20261030-1111"
        fake = FakeGit(existing=(old,))
        tag = self.run_preflight(fake, ["1111", "2222"])
        self.assertEqual(tag, "plan/historia/20261030-2222")
        self.assertIn(old, fake.remote_tags)
        self.assertNotIn(["tag", old, SHA], fake.calls)

    def test_stops_after_bounded_collisions_without_tagging(self):
        names = [f"plan/historia/20261030-{i:04x}" for i in range(MAX_ATTEMPTS)]
        fake = FakeGit(existing=names)
        with self.assertRaisesRegex(TagError, "bounded attempts"):
            self.run_preflight(fake, [f"{i:04x}" for i in range(MAX_ATTEMPTS)])
        self.assertFalse(any(call[0] in {"tag", "push"} for call in fake.calls))

    def test_verifies_exact_sha_and_fails_on_mismatch(self):
        fake = FakeGit(remote_sha="c" * 40)
        with self.assertRaisesRegex(TagError, "exact requested SHA"):
            self.run_publish(fake)
        self.assertIn("plan/historia/20261030-abcd", fake.remote_tags)

    def test_unexpected_local_tag_probe_error_fails_closed(self):
        fake = FakeGit(show_ref_code=128)
        with self.assertRaisesRegex(TagError, "local tag absence"):
            self.run_preflight(fake, ["abcd"])
        self.assertFalse(any(call[0] in {"tag", "push"} for call in fake.calls))

    def test_fetch_failure_stops_before_tag_or_push(self):
        fake = FakeGit(fetch_code=1)
        with self.assertRaisesRegex(TagError, "fetch"):
            self.run_preflight(fake, ["abcd"])
        self.assertIn(["fetch", "--no-tags", "origin", BRANCH], fake.calls)
        self.assertFalse(any(call[0] in {"tag", "push"} for call in fake.calls))

    def test_push_race_is_not_overwritten_or_retried(self):
        fake = FakeGit(push_race=True)
        with self.assertRaisesRegex(TagError, "git push"):
            self.run_publish(fake)
        self.assertIn("plan/historia/20261030-abcd", fake.remote_tags)
        self.assertNotIn("plan/historia/20261030-ef01", fake.remote_tags)
        self.assertEqual(sum(call[0] == "push" for call in fake.calls), 1)

    def test_publish_rechecks_preflight_name_before_tagging(self):
        tag = "plan/historia/20261030-abcd"
        fake = FakeGit(existing=(tag,))
        with self.assertRaisesRegex(TagError, "possible race"):
            self.run_publish(fake, tag)
        self.assertFalse(any(call[0] in {"tag", "push"} for call in fake.calls))

    def test_invalid_calendar_date_rejected_before_git(self):
        fake = FakeGit()
        with self.assertRaisesRegex(TagError, "calendar date"):
            self.run_preflight(fake, ["abcd"], date="20260230")
        self.assertEqual(fake.calls, [])


if __name__ == "__main__":
    unittest.main()

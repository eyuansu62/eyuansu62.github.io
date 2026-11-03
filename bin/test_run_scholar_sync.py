"""Exercise the scheduled runner's checkout guards with real local Git repos."""

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import run_scholar_sync as sync


class LocalCheckoutTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        self.repository = root / "checkout"
        self.repository.mkdir()
        self.origin = root / "origin.git"
        subprocess.run(["git", "init", "--bare", str(self.origin)], check=True, capture_output=True)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.file = self.repository / "example.txt"
        self.file.write_text("Original\n")
        self.git("add", "example.txt")
        self.git("commit", "-m", "Create test fixture")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "origin", "main")
        patcher = patch.object(sync, "ROOT", self.repository)
        patcher.start()
        self.addCleanup(patcher.stop)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repository, check=True, capture_output=True, text=True).stdout.strip()

    def test_clean_checkout_tolerates_unrelated_untracked_files(self):
        (self.repository / "unrelated.txt").write_text("Preserve me\n")
        before = self.git("rev-parse", "HEAD")
        sync.prepare_checkout()
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertEqual((self.repository / "unrelated.txt").read_text(), "Preserve me\n")

    def test_tracked_edits_are_preserved(self):
        self.file.write_text("User's work\n")
        with self.assertRaisesRegex(RuntimeError, "local changes"):
            sync.prepare_checkout()
        self.assertEqual(self.file.read_text(), "User's work\n")

    def test_other_branches_are_not_switched(self):
        self.git("switch", "-c", "codex/in-progress")
        with self.assertRaisesRegex(RuntimeError, "main checkout"):
            sync.prepare_checkout()
        self.assertEqual(self.git("branch", "--show-current"), "codex/in-progress")

    def test_unpublished_user_commits_are_not_pushed(self):
        remote_before = self.git("rev-parse", "origin/main")
        self.file.write_text("Not ready to publish\n")
        self.git("commit", "-am", "Private local fixture")
        with self.assertRaisesRegex(RuntimeError, "unpublished commits"):
            sync.prepare_checkout()
        remote_after = subprocess.check_output(["git", "--git-dir", str(self.origin), "rev-parse", "main"], text=True).strip()
        self.assertEqual(remote_after, remote_before)


if __name__ == "__main__":
    unittest.main()

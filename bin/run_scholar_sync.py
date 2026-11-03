#!/usr/bin/env python3
"""Run the local scheduled Scholar import and publish only its data changes."""

import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = ["_data/citations.yml", "_bibliography/scholar.bib"]
COMMIT_MESSAGE = """Keep the homepage current as Scholar adds papers

Import newly listed Scholar publications and refresh citation counts from
the local Mac, preserving curated publication metadata.

Constraint: Google Scholar rejects the GitHub-hosted runner
Confidence: high
Scope-risk: narrow
Tested: Offline Scholar sync regression tests and successful local fetch
"""


def run(args: list[str], *, capture: bool = False, timeout: int = 120) -> str:
    result = subprocess.run(
        args, cwd=ROOT, check=True, text=True, timeout=timeout,
        stdout=subprocess.PIPE if capture else None,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": "ssh -o BatchMode=yes"},
    )
    return result.stdout.strip() if capture else ""


def prepare_checkout() -> None:
    if run(["git", "branch", "--show-current"], capture=True) != "main":
        raise RuntimeError("Scholar sync requires the main checkout; leaving the current branch untouched.")
    if run(["git", "status", "--porcelain", "--untracked-files=no"], capture=True):
        raise RuntimeError("Tracked files have local changes; Scholar sync will not overwrite them.")
    run(["git", "fetch", "origin", "main"])
    if run(["git", "rev-list", "--count", "origin/main..HEAD"], capture=True) != "0":
        raise RuntimeError("Local main has unpublished commits; Scholar sync will not publish them.")
    run(["git", "merge", "--ff-only", "origin/main"])


def prepare_python() -> Path:
    environment = ROOT / ".venv"
    python = environment / "bin" / "python"
    if not python.exists():
        run([sys.executable, "-m", "venv", str(environment)])
    requirements = ROOT / "requirements.txt"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = environment / "scholar-requirements.sha256"
    if not stamp.exists() or stamp.read_text().strip() != digest:
        run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(requirements)], timeout=300)
        stamp.write_text(digest + "\n")
    return python


def main() -> None:
    # flock releases automatically even if a scheduled process is interrupted.
    key = hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
    with (Path(tempfile.gettempdir()) / f"scholar-sync-{key}.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another Scholar sync is already running.") from None
        prepare_checkout()
        python = prepare_python()
        run([str(python), "-m", "unittest", "discover", "-s", "bin", "-p", "test_update_scholar*.py"], timeout=60)
        run([str(python), "-u", "bin/update_scholar_citations.py", "--sync-publications", "--force"], timeout=300)
        changed = run(["git", "diff", "--name-only"], capture=True).splitlines()
        if set(changed) - set(DATA_FILES):
            raise RuntimeError("Unexpected source changes appeared during sync; nothing will be committed.")
        if not changed:
            print("Scholar sync succeeded; no publication or citation data changed.")
            return
        run(["git", "add", "--", *DATA_FILES])
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as message:
            message.write(COMMIT_MESSAGE)
            message.flush()
            run(["git", "-c", "user.name=Scholar Sync", "-c", "user.email=scholar-sync@users.noreply.github.com",
                 "commit", "--file", message.name])
        run(["git", "push", "origin", "HEAD:main"])
        print("Scholar data published:", run(["git", "rev-parse", "HEAD"], capture=True))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.SubprocessError, OSError) as error:
        print(f"Scholar sync stopped: {error}", file=sys.stderr)
        sys.exit(1)

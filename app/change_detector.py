"""Git-based change detection for the Book API documentation sync project."""

from __future__ import annotations

import subprocess
from pathlib import Path


class ChangeDetectionResult:
    """Encapsulates the result of comparing the API source with Git HEAD."""

    def __init__(self, status: str, message: str, changed: bool = False) -> None:
        self.status = status
        self.message = message
        self.changed = changed


def detect_api_change(repo_root: Path | str, api_path: Path | str) -> ChangeDetectionResult:
    """Compare app/api.py with HEAD and determine whether a relevant sync is needed.

    The baseline is the repository HEAD. We compare HEAD:app/api.py with the current
    app/api.py, including both staged and unstaged changes.
    """
    repo_root = Path(repo_root)
    api_path = repo_root / Path(api_path)

    if not api_path.exists():
        return ChangeDetectionResult(
            status="OPERATIONAL ERROR",
            message="API source file is missing: {0}".format(api_path),
            changed=False,
        )

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ChangeDetectionResult(
            status="OPERATIONAL ERROR",
            message="Git is not available or could not be executed.",
            changed=False,
        )

    if completed.returncode != 0:
        return ChangeDetectionResult(
            status="OPERATIONAL ERROR",
            message="Git HEAD is unavailable. Documentation synchronization cannot proceed safely.",
            changed=False,
        )

    try:
        diff = subprocess.run(
            ["git", "diff", "HEAD", "--", str(api_path.relative_to(repo_root))],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ChangeDetectionResult(
            status="OPERATIONAL ERROR",
            message="Git diff failed while checking API source changes.",
            changed=False,
        )

    if diff.returncode != 0:
        return ChangeDetectionResult(
            status="OPERATIONAL ERROR",
            message="Git diff failed while comparing app/api.py with HEAD.",
            changed=False,
        )

    if diff.stdout.strip() == "":
        return ChangeDetectionResult(
            status="NO CHANGE",
            message="No relevant API source changes detected relative to Git HEAD.",
            changed=False,
        )

    return ChangeDetectionResult(
        status="SUCCESS",
        message="Relevant API source changes detected relative to Git HEAD.",
        changed=True,
    )

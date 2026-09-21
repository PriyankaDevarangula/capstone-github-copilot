"""Menu-driven CLI for Book API documentation synchronization."""

from __future__ import annotations

import sys
from pathlib import Path

from app.change_detector import detect_api_change
from app.extractor import ExtractionError, extract_api_contract
from app.synchronizer import SynchronizationError, synchronize_documentation, write_document_atomically
from app.validator import DocumentationValidator


class AppRuntime:
    """Simple orchestration object for the CLI workflow."""

    def __init__(self, repo_root: str | Path, api_path: str | Path, docs_path: str | Path) -> None:
        self.repo_root = Path(repo_root)
        self.api_path = self.repo_root / api_path
        self.docs_path = self.repo_root / docs_path

    def run_sync(self) -> str:
        """Run the synchronization flow and return a status category."""
        change_result = detect_api_change(self.repo_root, self.api_path)
        if change_result.status == "OPERATIONAL ERROR":
            return "OPERATIONAL ERROR: {0}".format(change_result.message)
        if change_result.status == "NO CHANGE":
            return "NO CHANGE: {0}".format(change_result.message)

        try:
            contract = extract_api_contract(self.api_path)
        except ExtractionError as exc:
            return "VALIDATION ERROR: {0}".format(exc)

        try:
            updated = synchronize_documentation(self.docs_path, contract)
        except SynchronizationError as exc:
            return "VALIDATION ERROR: {0}".format(exc)

        validation = DocumentationValidator.validate_documentation(updated)
        if not validation["valid"]:
            return "VALIDATION ERROR: {0}".format("; ".join(validation["errors"]))

        try:
            write_document_atomically(self.docs_path, updated)
        except SynchronizationError as exc:
            return "OPERATIONAL ERROR: {0}".format(exc)

        return "SUCCESS: Documentation synchronized successfully."

    def validate_docs(self) -> str:
        """Validate the current documentation file without modifying it."""
        if not self.docs_path.exists():
            return "VALIDATION ERROR: Documentation file is missing: {0}".format(self.docs_path)

        try:
            markdown = self.docs_path.read_text(encoding="utf-8")
        except OSError as exc:
            return "OPERATIONAL ERROR: Unable to read documentation file: {0}".format(exc)

        result = DocumentationValidator.validate_documentation(markdown)
        if result["valid"]:
            return "SUCCESS: Documentation is valid."
        return "VALIDATION ERROR: {0}".format("; ".join(result["errors"]))


def print_menu() -> None:
    """Display the menu."""
    print("========================================")
    print(" Book API Documentation Sync")
    print("========================================")
    print("1. Synchronize Documentation")
    print("2. Validate Documentation")
    print("3. Exit")
    print()


def main() -> int:
    """Run the CLI program."""
    repo_root = Path(__file__).resolve().parent.parent
    runtime = AppRuntime(repo_root, "app/api.py", "docs/api.md")

    while True:
        print_menu()
        choice = input("Enter choice: ").strip()

        if choice == "1":
            print(runtime.run_sync())
        elif choice == "2":
            print(runtime.validate_docs())
        elif choice == "3":
            print("Exiting.")
            return 0
        else:
            print("VALIDATION ERROR: Invalid selection. Please choose 1, 2, or 3.")

        print()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nOPERATIONAL ERROR: Application interrupted by user.")
        raise SystemExit(1)
    except EOFError:
        print("\nVALIDATION ERROR: No input received. Exiting.")
        raise SystemExit(1)
